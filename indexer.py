import time
from pathlib import Path
from threading import Lock
import logging

# File extensions RepoLens can scan
SUPPORTED_EXTENSIONS = {
    ".py",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".json",
    ".md",
}


# Folders RepoLens should ignore
IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
}


# Cache configuration
CACHE_TTL_SECONDS = 10
MAX_CACHED_REPOSITORIES = 5

MAX_FILE_SIZE_BYTES = 1024 * 1024

# Maximum number of source files in one scan
MAX_REPO_FILES = 2000

# Maximum combined size of scanned source files: 20 MiB
MAX_REPO_TOTAL_BYTES = 20 * 1024 * 1024


class RepositoryLimitError(Exception):
    """Raised when a repository exceeds a scanning limit."""
    pass

logger = logging.getLogger(__name__)

# Stores recently scanned repositories
_scan_cache = {}

# Protects the cache from simultaneous access
_cache_lock = Lock()

# Statistics for testing our cache
_cache_hits = 0
_cache_misses = 0


def is_supported_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def should_ignore_path(file_path: Path) -> bool:
    for part in file_path.parts:
        if part in IGNORED_DIRS:
            return True

    return False




def _scan_repo_uncached(repo_path: str) -> list[dict]:
    """
    Scan a repository with per-file and
    repository-wide resource limits.
    """

    repo = Path(repo_path)

    if not repo.exists():
        raise FileNotFoundError(
            f"Repo path does not exist: {repo_path}"
        )

    if not repo.is_dir():
        raise NotADirectoryError(
            f"Repo path is not a folder: {repo_path}"
        )

    files = []
    total_bytes = 0

    for file_path in repo.rglob("*"):

        if file_path.is_symlink():
            continue

        if should_ignore_path(file_path):
            continue

        try:
            if not file_path.is_file():
                continue

            if not is_supported_file(file_path):
                continue

            file_size = file_path.stat().st_size

            # Ignore individual oversized files.
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.warning(
                    "Skipping oversized file: %s",
                    file_path,
                )
                continue

            # Stop before exceeding the file-count limit.
            if len(files) >= MAX_REPO_FILES:
                raise RepositoryLimitError(
                    f"Repository exceeds the limit of "
                    f"{MAX_REPO_FILES} source files."
                )

            # Stop before exceeding the total-size limit.
            if total_bytes + file_size > MAX_REPO_TOTAL_BYTES:
                raise RepositoryLimitError(
                    f"Repository exceeds the total source "
                    f"size limit of "
                    f"{MAX_REPO_TOTAL_BYTES // (1024 * 1024)} MiB."
                )

            content = file_path.read_text(
                encoding="utf-8"
            )

        except UnicodeError:
            logger.warning(
                "Skipping file with invalid encoding: %s",
                file_path,
            )
            continue

        except OSError as error:
            logger.warning(
                "Skipping unreadable file %s: %s",
                file_path,
                error,
            )
            continue

        files.append({
            "path": str(file_path),
            "content": content,
            "line_count": len(content.splitlines()),
        })

        total_bytes += file_size

    return files




def scan_repo(repo_path: str) -> list[dict]:
    """
    Return cached files if available and fresh.
    Otherwise, scan the repository again.
    """
    global _cache_hits, _cache_misses

    cache_key = str(Path(repo_path))

    with _cache_lock:
        current_time = time.monotonic()

        cached_entry = _scan_cache.get(cache_key)

        # Check whether the cache is still valid
        if cached_entry is not None:
            age = current_time - cached_entry["created_at"]

            if age < CACHE_TTL_SECONDS:
                _cache_hits += 1
                return cached_entry["files"]

        # Cache missing or expired: perform a real scan
        files = _scan_repo_uncached(repo_path)

        _cache_misses += 1

        # Limit the number of cached repositories
        if (
            cache_key not in _scan_cache
            and len(_scan_cache) >= MAX_CACHED_REPOSITORIES
        ):
            oldest_key = min(
                _scan_cache,
                key=lambda key: _scan_cache[key]["created_at"],
            )

            del _scan_cache[oldest_key]

        # Save the fresh scan in memory
        _scan_cache[cache_key] = {
            "created_at": time.monotonic(),
            "files": files,
        }

        return files


def get_cache_info() -> dict:
    """
    Return information about cache performance.
    """
    with _cache_lock:
        return {
            "hits": _cache_hits,
            "misses": _cache_misses,
            "cached_repositories": len(_scan_cache),
            "ttl_seconds": CACHE_TTL_SECONDS,
        }


def clear_repo_cache(repo_path: str) -> None:
    """
    Remove one repository's saved scan.
    The next request will scan it again.
    """
    cache_key = str(Path(repo_path))

    with _cache_lock:
        _scan_cache.pop(cache_key, None)


def search_files(
    files: list[dict],
    query: str,
    context_lines: int = 2,
) -> list[dict]:

    results = []

    for file in files:
        lines = file["content"].splitlines()

        for index, line in enumerate(lines):
            if query.lower() in line.lower():
                start = max(0, index - context_lines)
                end = min(len(lines), index + context_lines + 1)

                context = []

                for context_index in range(start, end):
                    context.append({
                        "line_number": context_index + 1,
                        "line": lines[context_index],
                        "is_match": context_index == index,
                    })

                results.append({
                    "path": file["path"],
                    "line_number": index + 1,
                    "line": line.strip(),
                    "context": context,
                })

    return results
