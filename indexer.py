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
    ".c",
    ".ts",
    ".tsx",
    ".json",
    ".md",
}


IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    "dist",
    "build",
}
# A list of supported suffixes or files, so when we do scan for a file it returns true or false that it supports the file

def is_supported_file(file_path: Path) -> bool:# It checks wether what we file we input is supported in our checker, check list.
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

def should_ignore_path(file_path:Path) -> bool:
    for part in file_path.parts:
        if part in IGNORED_DIRS:
            return True

    return False



def scan_repo(repo_path: str) -> list[dict]:  # It will return as a string
    repo = Path(repo_path)  # will convert your input path into Path("blah")
    if not repo.exists():
        raise FileNotFoundError(f"Repo path does not exist: {repo_path}")  # self explanatory

    if not repo.is_dir():
        raise NotADirectoryError(f"Repo path is not a folder: {repo_path}")  # self explanatory

    files = []  # an empty list that we will fill with data

    for file_path in repo.rglob("*"):  # "r" in "rglob" mean recursive, so it will scan all the files in the repo and subfolders
        if should_ignore_path(file_path):  #if file belongs to ignored file path, continue, skip it. yuh
            continue

        if file_path.is_file() and is_supported_file(file_path):# It asks, is it a file? AND is it supported?
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
                #Saying, open the file and read it to me, using the encoding above, and store it into 'content'
                #Read the file and if it fails because of text encoding, skip it and keep going


            lines = content.splitlines()

            files.append({  #This adds a dictionary to the "files" list. where "path" stores where the file is which is the path and obviously content, is what is inside the said "files"
                "path": str(file_path),
                "content": content,
                "line_count": len(lines),
            })

    return files  #gives you the files when called function


def search_files(files: list[dict], query: str, context_lines: int = 2) -> list[dict]:  #takes in file, query, and context lines. context_lines: int = 2 will allow you too see above 2 and down 2 lines
    results = []  # an empty list that we will fill with data

    for file in files:
        lines = file["content"].splitlines()

        for index, line in enumerate(lines):
            if query.lower() in line.lower():
                start = max(0, index - context_lines)
                end = min(len(lines), index + context_lines + 1)

                context = []

                for context_index in range(start, end): # results now capture extra nearby lines
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




