import pytest

import api
import indexer

from fastapi.testclient import TestClient

from api import app
from indexer import (
    scan_repo,
    search_files,
    clear_repo_cache,
    get_cache_info,
    MAX_FILE_SIZE_BYTES,
)
from symbols import analyze_python_file
from dependencies import build_dependency_graph
from pathlib import Path



# Allows us to make test requests to the FastAPI application.
client = TestClient(app)


# TEST 1: File scanning and ignored folders
def test_scanner_finds_code_and_ignores_unwanted_files(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    code_file = repo / "auth.py"
    code_file.write_text(
        "def login_user():\n    return True\n",
        encoding="utf-8",
    )

    (repo / "notes.txt").write_text(
        "This is not a supported file.",
        encoding="utf-8",
    )

    ignored_folder = repo / "node_modules"
    ignored_folder.mkdir()

    (ignored_folder / "fake.js").write_text(
        "function login() {}",
        encoding="utf-8",
    )

    files = scan_repo(str(repo))

    assert len(files) == 1
    assert files[0]["path"] == str(code_file)
    assert files[0]["line_count"] == 2


# TEST 2: Case-insensitive text search
def test_search_finds_matches_and_context(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    (repo / "auth.py").write_text(
        "first line\n"
        "def Login_User():\n"
        "    return True\n",
        encoding="utf-8",
    )

    files = scan_repo(str(repo))
    results = search_files(files, "LOGIN", context_lines=1)

    assert len(results) == 1
    assert results[0]["line_number"] == 2
    assert "Login_User" in results[0]["line"]
    assert len(results[0]["context"]) == 3

    matching_lines = [
        line for line in results[0]["context"]
        if line["is_match"]
    ]

    assert len(matching_lines) == 1
    assert matching_lines[0]["line_number"] == 2


# TEST 3: Missing repository handling
def test_scanner_rejects_missing_repository(tmp_path):
    missing_repo = tmp_path / "does_not_exist"

    with pytest.raises(FileNotFoundError):
        scan_repo(str(missing_repo))


# TEST 4: Cache reuse and manual refresh
def test_cache_can_be_cleared(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    code_file = repo / "example.py"
    code_file.write_text("value = 1\n", encoding="utf-8")

    before = get_cache_info()

    first_scan = scan_repo(str(repo))

    # Change the file after the first scan.
    code_file.write_text("value = 2\n", encoding="utf-8")

    # The recent cached scan should still contain the old text.
    second_scan = scan_repo(str(repo))

    assert first_scan[0]["content"] == "value = 1\n"
    assert second_scan[0]["content"] == "value = 1\n"

    # Remove the cache and scan again.
    clear_repo_cache(str(repo))

    third_scan = scan_repo(str(repo))

    assert third_scan[0]["content"] == "value = 2\n"

    after = get_cache_info()

    assert after["hits"] >= before["hits"] + 1


# TEST 5: Python function, class, and import analysis
def test_symbol_analyzer():
    content = (
        "import os\n"
        "from auth import login_user\n"
        "\n"
        "class UserService:\n"
        "    def authenticate(self):\n"
        "        return login_user()\n"
    )

    file = {
        "path": "service.py",
        "content": content,
        "line_count": len(content.splitlines()),
    }

    result = analyze_python_file(file)

    names = {symbol["name"] for symbol in result["symbols"]}

    assert "UserService" in names
    assert "authenticate" in names
    assert len(result["imports"]) == 2
    assert result["parse_error"] is None


# TEST 6: Dependency detection
def test_dependency_graph(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    (repo / "auth.py").write_text(
        "def login_user():\n    return True\n",
        encoding="utf-8",
    )

    (repo / "routes.py").write_text(
        "from auth import login_user\n",
        encoding="utf-8",
    )

    (repo / "database.py").write_text(
        "users = []\n",
        encoding="utf-8",
    )

    graph = build_dependency_graph(str(repo))

    assert graph["files_analyzed"] == 3
    assert graph["dependencies_found"] == 1

    assert {
        "source": "routes.py",
        "target": "auth.py",
    } in graph["edges"]


# TEST 7: FastAPI search endpoint
def test_api_search_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("REPOLENS_ALLOWED_ROOT", str(tmp_path))
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    (repo / "auth.py").write_text(
        "def login_user():\n    return True\n",
        encoding="utf-8",
    )

    response = client.get(
        "/search",
        params={
            "repo_path": str(repo),
            "query": "login",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["files_scanned"] == 1
    assert data["results_found"] == 1
    assert data["results"][0]["line_number"] == 1


# TEST 8: FastAPI rejects invalid query parameters
def test_api_rejects_empty_search_query(tmp_path, monkeypatch):
    monkeypatch.setenv("REPOLENS_ALLOWED_ROOT", str(tmp_path))
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    response = client.get(
        "/search",
        params={
            "repo_path": str(repo),
            "query": "",
        },
    )

    assert response.status_code == 422



# SECURITY TEST: Every repository endpoint must reject
# paths outside the approved workspace.

@pytest.mark.parametrize(
    "method, endpoint, extra_params",
    [
        ("GET", "/search", {"query": "login"}),
        ("GET", "/files", {}),
        ("GET", "/stats", {}),
        ("GET", "/symbols", {}),
        ("GET", "/dependencies", {}),
        ("GET", "/file", {"file_path": "secret.py"}),
        ("POST", "/refresh", {}),
    ],
)
def test_api_blocks_outside_repositories(
    tmp_path,
    monkeypatch,
    method,
    endpoint,
    extra_params,
):
    allowed = tmp_path / "allowed"
    allowed.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()

    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(allowed),
    )

    response = client.request(
        method,
        endpoint,
        params={
            "repo_path": str(outside),
            **extra_params,
        },
    )

    assert response.status_code == 403


# SECURITY TEST: A symlinked repository must not
# bypass the allowed-directory restriction.

def test_api_blocks_symlinked_repository(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()

    link = allowed / "linked_repo"
    link.symlink_to(outside, target_is_directory=True)

    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(allowed),
    )

    response = client.get(
        "/files",
        params={"repo_path": str(link)},
    )

    assert response.status_code == 403


# SECURITY TEST: The scanner must ignore symlinked
# source files even if they have supported extensions.

def test_scanner_skips_symlinked_files(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    outside_file = tmp_path / "private.py"
    outside_file.write_text(
        "secret_value = 'example'\n",
        encoding="utf-8",
    )

    link = repo / "linked_file.py"
    link.symlink_to(outside_file)

    files = scan_repo(str(repo))

    assert files == []

    # TEST 18: Oversized files should be skipped.
def test_scanner_skips_oversized_files(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    # A small, valid Python file.
    (repo / "small.py").write_text(
        "value = 42\n",
        encoding="utf-8",
    )

    # A source file larger than our configured limit.
    (repo / "huge.py").write_bytes(
        b"x" * (MAX_FILE_SIZE_BYTES + 1)
    )

    files = scan_repo(str(repo))

    # Only the small file should be returned.
    assert len(files) == 1
    assert Path(files[0]["path"]).name == "small.py"

# TEST 19: Invalid UTF-8 should not crash the scanner.
def test_scanner_skips_invalid_encoding(tmp_path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    # This file contains invalid UTF-8 bytes.
    (repo / "damaged.py").write_bytes(
        b"\xff\xfe\xfa"
    )

    # This file should still be scanned.
    (repo / "working.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    files = scan_repo(str(repo))

    assert len(files) == 1
    assert Path(files[0]["path"]).name == "working.py"

# TEST 20: A file read error should not stop the scan.
def test_scanner_handles_permission_errors(
        tmp_path,
        monkeypatch,
):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    protected_file = repo / "protected.py"
    protected_file.write_text(
        "secret = 123\n",
        encoding="utf-8",
    )

    working_file = repo / "working.py"
    working_file.write_text(
        "value = 42\n",
        encoding="utf-8",
    )

    # Save the original method.
    original_read_text = Path.read_text

    # Simulate a permission error for one particular file.
    def fake_read_text(path, *args, **kwargs):
        if path == protected_file:
            raise PermissionError("Access denied")

        return original_read_text(
            path,
            *args,
            **kwargs,
        )

    # Temporarily replace Path.read_text during this test.
    monkeypatch.setattr(
        Path,
        "read_text",
        fake_read_text,
    )

    files = scan_repo(str(repo))

    # The protected file is skipped.
    # The working file is still scanned.
    assert len(files) == 1
    assert Path(files[0]["path"]).name == "working.py"


# TEST 21: Reject repositories with too many source files.
def test_repository_file_count_limit(tmp_path, monkeypatch):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    for number in range(3):
        (repo / f"file_{number}.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(indexer, "MAX_REPO_FILES", 2)

    with pytest.raises(indexer.RepositoryLimitError):
        scan_repo(str(repo))


# TEST 22: Reject repositories exceeding total source size.
def test_repository_total_size_limit(tmp_path, monkeypatch):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    (repo / "first.py").write_text("x" * 30, encoding="utf-8")
    (repo / "second.py").write_text("y" * 30, encoding="utf-8")

    monkeypatch.setattr(
        indexer,
        "MAX_REPO_TOTAL_BYTES",
        50,
    )

    with pytest.raises(indexer.RepositoryLimitError):
        scan_repo(str(repo))


# TEST 23: API should return a useful repository-limit error.
def test_api_repository_limit_error(tmp_path, monkeypatch):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    for number in range(3):
        (repo / f"file_{number}.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )

    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(tmp_path),
    )

    monkeypatch.setattr(indexer, "MAX_REPO_FILES", 2)

    response = client.get(
        "/files",
        params={"repo_path": str(repo)},
    )

    assert response.status_code == 422
    assert "limit" in response.json()["detail"].lower()


# TEST 24: A missing repository returns HTTP 404.
def test_api_missing_repository(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(tmp_path),
    )

    missing_repo = tmp_path / "missing_project"

    response = client.get(
        "/files",
        params={"repo_path": str(missing_repo)},
    )

    assert response.status_code == 404
    assert "detail" in response.json()


# TEST 25: A file cannot be used as a repository folder.
def test_api_rejects_non_directory(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(tmp_path),
    )

    file_path = tmp_path / "not_a_folder.py"
    file_path.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    response = client.get(
        "/files",
        params={"repo_path": str(file_path)},
    )

    assert response.status_code == 400
    assert "detail" in response.json()


# TEST 26: Opening a missing file returns HTTP 404.
def test_api_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(tmp_path),
    )

    repo = tmp_path / "demo_repo"
    repo.mkdir()

    response = client.get(
        "/file",
        params={
            "repo_path": str(repo),
            "file_path": str(repo / "missing.py"),
        },
    )

    assert response.status_code == 404
    assert "detail" in response.json()


# TEST 27: Simulated permission error returns HTTP 403.
def test_api_handles_permission_error(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(tmp_path),
    )

    repo = tmp_path / "demo_repo"
    repo.mkdir()

    def simulate_permission_error(repo_path):
        raise PermissionError("Simulated access denied")

    monkeypatch.setattr(
        api,
        "scan_repo",
        simulate_permission_error,
    )

    response = client.get(
        "/files",
        params={"repo_path": str(repo)},
    )

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# TEST 28: Unexpected filesystem error returns HTTP 500.
def test_api_handles_filesystem_error(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "REPOLENS_ALLOWED_ROOT",
        str(tmp_path),
    )

    repo = tmp_path / "demo_repo"
    repo.mkdir()

    def simulate_filesystem_error(repo_path):
        raise OSError("Simulated filesystem failure")

    monkeypatch.setattr(
        api,
        "scan_repo",
        simulate_filesystem_error,
    )

    response = client.get(
        "/files",
        params={"repo_path": str(repo)},
    )

    assert response.status_code == 500

    # Verify that internal error details aren't exposed.
    assert "Simulated filesystem failure" not in str(
        response.json()
    )
