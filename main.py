import sys
from indexer import scan_repo, search_files

def main():
    if len(sys.argv) != 3:
        print("usage: python main.py <repo_path> <search_query>")
        print("Example: python main.py sample_repo login")
        return

    repo_path = sys.argv[1] #argv(0) is main.py , 1 is sample_repo, 2 is login
    query = sys.argv[2]

    files = scan_repo(repo_path)
    results = search_files(files, query)

    total_lines = 0

    for file in files:
        total_lines += file["line_count"]

    print("RepoLens Search Summary")
    print("-----------------------")
    print(f"Repository: {repo_path}")
    print(f"Query: {query}")
    print(f"Files scanned: {len(files)}")
    print(f"Lines scanned: {total_lines}")
    print(f"Results found: {len(results)}")
    print()

    if not results:
        print("No results found.")
        return

    for result in results:
        print(result["path"])

        for context_line in result["context"]:
            marker = ">" if context_line["is_match"] else " "
            print(f"{marker} {context_line['line_number']}: {context_line['line']}")

        print()

if __name__ == "__main__":
    main()