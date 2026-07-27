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

    print(f"Scanned {len(files)} file(s)")
    print(f"Found {len(results)} result(s)")
    print()


    for result in results:
        print(result["path"])
        print(f"line {result['line_number']}: {result['line']}")
        print()

if __name__ == "__main__":
    main()