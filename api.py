from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from indexer import scan_repo, search_files #Reusing what we wrote in indexer.py, so we can use it here in the API
from symbols import extract_symbols
from dependencies import build_dependency_graph


app = FastAPI(
    title="RepoLens API",
    description="A code search API that scans a repository and returns matching code lines with context.",
    version="1.0.1",
)

@app.get("/") # SO when you run the API, it will automatically open this page, because it is the root page, returning the message bellow, showing how it works. like in html, "/" is default page or new blank page, something like that
def root():
    return {
        "message": "RepoLens API is running",
        "routes": {
            "health": "/health",
            "search": "/search?repo_path=sample_repo&query=login",
            "files": "/files?repo_path=sample_repo",
            "stats": "/stats?repo_path=sample_repo",
            "symbols": "/symbols?repo_path=sample_repo",
            "docs": "/docs",
        }
    }

@app.get("/health") #when runnin the API, you can use "/health" right after the url to check if the API is running.
def health_check():
    return {
        "status": "ok"
    }

@app.get("/search") #
def search_repo(
        repo_path: str = Query(..., description="Path to the repository folder to scan"),
        query: str = Query(..., min_length=1, description="Search term to look for"),
        context_lines: int = Query(
            2,
            ge=0, #Greater than or equal to 0, so no negative numbers.
            le=10, #less than or equal to 10, so no more than 10 lines of context, because it will be too much and will make the API slow.
            description= "Number of lines to show before and after each match",
        ),
): #sad face

    try: #anything that doesn't work in the try block, will be caught in the except block, and will return a 404 error with the message of what went wrong
        files = scan_repo(repo_path)
        results = search_files(files, query, context_lines=context_lines)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error))

    total_lines = 0

    for file in files:
        total_lines += file["line_count"]

    return {
        "repository": repo_path,
        "query": query,
        "context_lines": context_lines,
        "files_scanned": len(files),
        "lines_scanned": total_lines,
        "results_found": len(results),
        "results": results
    }

@app.get("/files")
def list_files(
        repo_path: str = Query(..., descritpion="Path to the repository folder to scan"),
):
    try:
        files = scan_repo(repo_path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error))

    file_list = []

    for file in files:
        file_list.append({
            "path": file["path"],
            "line_count": file["line_count"],
        })

    return {
        "repository": repo_path,
        "files_found": len(file_list),
        "files": file_list
    }

@app.get("/stats")
def get_repo_stats(
        repo_path: str = Query(..., description="Path to the repository folder to scan"),
):
    try:
        files = scan_repo(repo_path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error))

    total_lines = 0

    for file in files:
        total_lines += file["line_count"]

    return {
        "repository": repo_path,
        "files_scanned": len(files),
        "lines_scanned": total_lines,
    }

@app.get("/symbols")
def get_symbols(
        repo_path: str = Query(..., description="Path to the repository folder to scan"),
):
    try:
        analyzed_files = extract_symbols(repo_path)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error))

    total_symbols = 0
    total_imports = 0

    for file in analyzed_files:
        total_symbols += len(file["symbols"])
        total_imports += len(file["imports"])

    return {
        "repository": repo_path,
        "python_files_analyzed": len(analyzed_files),
        "symbols_found": total_symbols,
        "imports_found": total_imports,
        "files": analyzed_files,
    }

@app.get("/dependencies")
def get_dependencies(
    repo_path: str = Query(..., description="Repository folder to analyze"),
):
    try:
        graph = build_dependency_graph(repo_path)

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return graph



@app.get("/file")
def get_file(
    repo_path: str = Query(..., description="Repository folder"),
    file_path: str = Query(..., description="File to open"),
):
    try:
        files = scan_repo(repo_path)

    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))

    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error))

    for file in files:
        if file["path"] == file_path:
            lines = file["content"].splitlines()

            numbered_lines = []

            for line_number, text in enumerate(lines, start=1):
                numbered_lines.append({
                    "line_number": line_number,
                    "text": text,
                })

            return {
                "repository": repo_path,
                "path": file_path,
                "line_count": len(lines),
                "lines": numbered_lines,
            }

    raise HTTPException(
        status_code=404,
        detail="File not found among the scanned repository files.",
    )



app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")







