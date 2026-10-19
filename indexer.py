
import time
from pathlib import Path
from threading import Lock


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
    Scan a repository directly from disk.
    This is our original scanning logic.
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

    for file_path in repo.rglob("*"):

        # Do not read symbolic links.
        if file_path.is_symlink():
            continue

        if should_ignore_path(file_path):
            continue

        if file_path.is_file() and is_supported_file(file_path):
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            lines = content.splitlines()

            files.append({
                "path": str(file_path),
                "content": content,
                "line_count": len(lines),
            })

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
