
from pathlib import Path

from symbols import extract_symbols


def build_dependency_graph(repo_path: str) -> dict:
    # Step 1: Find the repository and analyze its Python files.
    repo_root = Path(repo_path).resolve()
    analyzed_files = extract_symbols(str(repo_root))

    # Step 2: Create a lookup between Python modules and file paths.
    module_to_file = {}
    nodes = []

    for file in analyzed_files:
        relative_path = Path(file["path"]).relative_to(repo_root)
        file_name = relative_path.as_posix()

        module_parts = list(relative_path.with_suffix("").parts)

        if module_parts[-1] == "__init__":
            module_parts.pop()

        module_name = ".".join(module_parts)

        if module_name:
            module_to_file[module_name] = file_name

        nodes.append({
            "id": file_name,
            "label": file_name,
        })

    # Step 3: Discover dependencies from import statements.
    edges = []
    seen_edges = set()

    for file in analyzed_files:
        source = Path(file["path"]).relative_to(repo_root).as_posix()

        for imported in file["imports"]:
            if imported["type"] == "import":
                candidates = [imported["module"]]

            else:
                module = imported["module"] or ""
                imported_name = imported["name"]
                level = imported.get("level", 0)

                if level > 0:
                    parent_parts = list(Path(source).parent.parts)
                    levels_up = level - 1

                    if levels_up > len(parent_parts):
                        continue

                    package_parts = parent_parts[:len(parent_parts) - levels_up]

                    if module:
                        package_parts.extend(module.split("."))

                    module = ".".join(package_parts)

                full_name = (
                    f"{module}.{imported_name}"
                    if module else imported_name
                )

                candidates = [full_name, module]

            # Step 4: Find the corresponding file inside this repo.
            target = None

            for candidate in candidates:
                if candidate in module_to_file:
                    target = module_to_file[candidate]
                    break

            # Step 5: Save each dependency only once.
            if target and target != source:
                connection = (source, target)

                if connection not in seen_edges:
                    edges.append({
                        "source": source,
                        "target": target,
                    })

                    seen_edges.add(connection)

    nodes.sort(key=lambda node: node["id"])
    edges.sort(key=lambda edge: (edge["source"], edge["target"]))

    return {
        "repository": repo_path,
        "files_analyzed": len(nodes),
        "dependencies_found": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
