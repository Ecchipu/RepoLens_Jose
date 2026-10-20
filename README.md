# RepoLens

**A local code search and repository analysis tool built with Python, FastAPI, and vanilla JavaScript.**

RepoLens helps developers explore unfamiliar codebases by searching source files, identifying Python functions and classes, viewing import dependencies, and navigating code through a browser-based interface.

The project focuses on code analysis, backend API design, performance optimization, automated testing, and safe local filesystem access.

## Features

- **Code Search:** Find text across supported source files with line numbers and surrounding context.
- **File Explorer:** Browse source files and open their full contents in a code viewer.
- **Python Symbol Analysis:** Identify functions, classes, and imports using Python's Abstract Syntax Tree (AST) module.
- **Dependency Visualization:** Explore relationships between local Python modules using an interactive dependency graph.
- **Code Navigation:** Open matching files and jump to specific lines or function definitions.
- **Repository Statistics:** View file counts, line counts, and repository information.
- **Scan Caching:** Reuse recently scanned repository contents to reduce unnecessary disk reads.
- **Manual Refresh:** Clear cached scans and reload updated source files.
- **Filesystem Restrictions:** Restrict repository access to an approved workspace.
- **Resource Limits:** Limit the number and combined size of source files processed.
- **Automated Testing:** Test core scanning, API, caching, analysis, security, and error-handling functionality using pytest.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend implementation |
| FastAPI | HTTP API and frontend hosting |
| Python AST | Static Python code analysis |
| HTML5 | Frontend structure |
| CSS3 | Interface styling |
| JavaScript | Browser interaction and visualizations |
| SVG | Interactive dependency graph |
| pytest | Automated testing |
| Git | Version control |

## Project Structure

```text
RepoLens_Jose/
├── api.py
├── main.py
├── indexer.py
├── symbols.py
├── dependencies.py
├── security.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── sample_repo/
├── tests/
│   └── test_repolens.py
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

## Installation

**Requirements:** Python 3.12 and a terminal. Git is recommended.

### Windows

Clone or download the repository, then open a terminal in its root directory.

Create a virtual environment:

```powershell
py -3.12 -m venv .venv-win
```

Install dependencies:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Start the FastAPI development server:

```powershell
.\.venv-win\Scripts\python.exe -m fastapi dev api.py
```

### macOS / Linux

Create a virtual environment:

```bash
python3.12 -m venv .venv
```

Install dependencies:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

Start the application:

```bash
.venv/bin/python -m fastapi dev api.py
```

## Using RepoLens

With the server running, open:

**http://127.0.0.1:8000/app/**

To explore the included example project, enter:

- Repository path: `sample_repo`
- Search query: `login`
- Context lines: `2`

Click **Search Code** to find matching code.

Use **View Files** to browse the repository, **View Symbols** to inspect Python definitions, and **View Dependencies** to explore local module relationships.

Click a filename or function name to open the source viewer. Use **Refresh Repository** after editing files to update the cached scan.

FastAPI also provides interactive API documentation at:

**http://127.0.0.1:8000/docs**

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application health |
| GET | `/search` | Search source code |
| GET | `/files` | List supported repository files |
| GET | `/stats` | Retrieve repository statistics |
| GET | `/symbols` | Analyze Python functions, classes, and imports |
| GET | `/dependencies` | Retrieve local Python dependency relationships |
| GET | `/file` | Retrieve numbered source file contents |
| POST | `/refresh` | Clear and refresh the repository scan cache |

Repository endpoints accept a `repo_path` parameter. Search and file-viewer endpoints accept additional parameters.

## Supported Source Files

RepoLens supports the following file extensions:

`.py`, `.cpp`, `.c`, `.h`, `.hpp`, `.html`, `.css`, `.js`, `.ts`, `.tsx`, `.json`, and `.md`.

Text search and file viewing support these extensions. AST-based symbol analysis and import dependency detection are currently focused on Python.

## Performance and Safety

RepoLens uses a 10-second in-memory scan cache to reduce repeated filesystem work.

Default scan limits include:

| Limit | Value |
|---|---|
| Individual file size | 1 MiB |
| Number of scanned source files | 2,000 |
| Combined source file size | 20 MiB |

Oversized individual files and unreadable files are skipped. Repositories exceeding the overall scan limits are rejected with an API error.

By default, RepoLens restricts repository access to its application directory. The approved workspace can be changed through the `REPOLENS_ALLOWED_ROOT` environment variable.

**Security note:** RepoLens is intended for trusted local development. The application does not currently provide user authentication and has not been hardened for public internet deployment. Only scan repositories that you trust.

## Automated Testing

Run the automated test suite from the project root:

### Windows

```powershell
.\.venv-win\Scripts\python.exe -m pytest -v
```

### macOS / Linux

```bash
.venv/bin/python -m pytest -v
```

The project currently includes **28 passing automated test cases**, verified on Windows with Python 3.12.3.

Tests cover file scanning, searching, caching, Python symbol analysis, dependency detection, API validation, filesystem access restrictions, symbolic links, resource limits, and error handling.

## Architecture

RepoLens separates its functionality into several modules:

- `indexer.py` handles repository scanning, file filtering, searching, resource limits, and caching.
- `symbols.py` uses Python AST to analyze functions, classes, and imports.
- `dependencies.py` builds relationships between local Python modules.
- `security.py` validates requested repository paths against the allowed workspace.
- `api.py` exposes the application through FastAPI.
- `frontend/` contains the browser interface and dependency visualization.
- `tests/` contains automated regression and security tests.

The browser communicates with FastAPI through HTTP requests, and FastAPI uses the analysis modules to process local repositories.

## Future Improvements

Potential future features include:

- Syntax highlighting in the source viewer
- More advanced repository navigation
- Improved dependency resolution
- Support for symbol analysis in additional programming languages
- Persistent indexing for larger repositories
- Semantic code search
- Additional automated performance and security tests

## Project Purpose

RepoLens was developed as a software engineering portfolio project to practice full-stack development, modular architecture, static code analysis, API design, testing, caching, and filesystem security.

The project demonstrates how a Python backend and a JavaScript frontend can work together to create a practical developer tool.