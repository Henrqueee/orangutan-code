"""Gathers project context (directory tree) to send to the LLM."""

import os

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".env", "dist", "build", ".tox", ".mypy_cache", ".pytest_cache",
    "egg-info", ".eggs", ".idea", ".vscode",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db",
}


def build_directory_tree(root: str, max_depth: int = 4) -> str:
    """Build a text representation of the directory tree starting from root."""
    lines: list[str] = []
    root = os.path.abspath(root)
    base_name = os.path.basename(root) or root

    lines.append(f"{base_name}/")
    _walk_tree(root, "", lines, current_depth=0, max_depth=max_depth)

    return "\n".join(lines)


def _walk_tree(
    path: str,
    prefix: str,
    lines: list[str],
    current_depth: int,
    max_depth: int,
) -> None:
    if current_depth >= max_depth:
        return

    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return

    dirs = []
    files = []

    for entry in entries:
        if entry.startswith(".") and entry in IGNORE_FILES:
            continue
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            if entry not in IGNORE_DIRS and not entry.endswith(".egg-info"):
                dirs.append(entry)
        else:
            if entry not in IGNORE_FILES:
                files.append(entry)

    all_entries = [(d, True) for d in dirs] + [(f, False) for f in files]

    for i, (name, is_dir) in enumerate(all_entries):
        is_last = i == len(all_entries) - 1
        connector = "└── " if is_last else "├── "
        display = f"{name}/" if is_dir else name
        lines.append(f"{prefix}{connector}{display}")

        if is_dir:
            extension = "    " if is_last else "│   "
            _walk_tree(
                os.path.join(path, name),
                prefix + extension,
                lines,
                current_depth + 1,
                max_depth,
            )
