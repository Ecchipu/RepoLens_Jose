from fastapi import FastAPI, HTTPException, Query

from indexer import scan_repo, search_files #Reusing what we wrote in indexer.py, so we can use it here in the API

app = FastAPI(
    title="RepoLens API",
    description="A code search API that scans a repository and returns matching code lines with context.",
    version="1.0.0",
)

@app.get("/") # SO when you run the API, it will automatically open this page, because it is the root page, returning the message bellow, showing how it works. like in html, "/" is default page or new blank page, something like that
def root():
    return {
        "message": "RepoLens API is running",
        "try": "/search?repo_path=sample_repo&query=login",
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
):
    try: #anything that doesn't work in the try block, will be caught in the except block, and will return a 404 error with the message of what went wrong
        files = scan_repo(repo_path)
        results = search_files(files,query)
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
        "files_scanned": len(files),
        "lines_scanned": total_lines,
        "results_found": len(results),
        "results": results
    }