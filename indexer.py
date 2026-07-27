from pathlib import Path

# Imports pathlib so we can utitlize "Path" to scan the repo

SUPPORTED_EXTENSIONS = {
    ".py",
    ".cpp",
    ".h",
    ".hpp",
    ".html",
    ".css",
    ".js",
}


# A list of supported suffixes or files, so when we do scan for a file it returns true or false that it supports the file

def is_supported_file(file_path: Path) -> bool:
    return file_path.suffix in SUPPORTED_EXTENSIONS


# It checks wether what we file we input is supported in our checker, check list.


def scan_repo(repo_path: str) -> list[dict]:  # It will return as a string
    repo = Path(repo_path)  # will convert your input path into Path("blah")
    if not repo.exists():
        raise FileNotFoundError(f"Repo path does not exist: {repo_path}")  # self explanatory

    if not repo.is_dir():
        raise NotADirectoryError(f"Repo path is not a folder: {repo_path}")  # self explanatory

    files = []  # an empty list that we will fill with data

    for file_path in repo.rglob(
            "*"):  # "r" in "rglob" mean recursive, so it will scan all the files in the repo and subfolders
        if file_path.is_file() and is_supported_file(file_path):  # It asks, is it a file? AND is it supported?
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            # Saying, open the file and read it to me, using the encoding above, and store it into 'content'
            # Read the file and if it fails because of text encoding, skip it and keep going

            files.append({ #This adds a dictionary to the "files" list. where "path" stores where the file is which is the path and obviously content, is what is inside the said "files"
                "path": str(file_path),
                "content": content,
            })

    return files #gives you the files when called function


def search_files(files: list[dict], query: str) -> list[dict]: #Searches through the file list for matches
    results = [] #will store every match we find, adding to the list with every result.

    for file in files:
        lines = file["content"].splitlines() #this splitlines function makes the two outcomes come in two separate lines as said in function.

        for line_number, line in enumerate(lines, start=1): #amkes it so it reads as line 1 to #
            if query.lower() in line.lower(): #so it makes it incase sensitive, so when we look up something with upper or lower case, H h, it will still find it.
                results.append({
                    "path": file["path"],
                    "line_number": line_number,
                    "line": line.strip(),
                })

    return results #the wesults




