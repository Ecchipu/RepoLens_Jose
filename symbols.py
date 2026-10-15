import ast
from pathlib import Path

from indexer import scan_repo



def analyze_python_file(file: dict) -> dict:
    path = file["path"]
    content = file["content"]

    try:
        tree = ast.parse(content)
    except SyntaxError as error:
        return {
            "path" : path,
            "language": "python",
            "line_count": file["line_count"],
            "symbols": [],
            "imports": [],
            "parse_error": str(error),
        }

    symbols = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            symbols.append({
                "type": "function",
                "name": node.name,
                "line_number": node.lineno,
                "end_line_number": getattr(node, "end_lineno", node.lineno),
            })

        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append({
                "type": "async_function",
                "name": node.name,
                "line_number": node.lineno,
                "end_line_number": getattr(node, "end_lineno", node.lineno),
            })

        elif isinstance(node, ast.ClassDef):
            symbols.append({
                "type": "class",
                "name": node.name,
                "line_number": node.lineno,
                "end_line_number": getattr(node, "end_lineno", node.lineno),
            })

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "type": "import",
                    "module": alias.name,
                    "alias": alias.asname,
                    "line_number": node.lineno,
                })

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append({
                    "type": "from_import",
                    "module": node.module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "level": node.level,
                    "line_number": node.lineno,
                })

    return {
        "path": path,
        "language": "python",
        "line_count": file["line_count"],
        "symbols": symbols,
        "imports": imports,
        "parse_error": None,
    }

def extract_symbols(repo_path: str) -> list[dict]:
    files = scan_repo(repo_path)
    analyzed_files = []

    for file in files:
        file_path = Path(file["path"])

        if file_path.suffix.lower() == ".py":
            analyzed_files.append(analyze_python_file(file))


    return analyzed_files

