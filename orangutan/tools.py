"""Tool execution engine - handles all tool operations for Orangutan Code."""

import fnmatch
import os
import subprocess
import sys

from orangutan.ask_tool import ask_user
from orangutan.config import config_path, read_config, write_config


# Step tracking output
def _step(tool_name: str, detail: str) -> None:
    """Print a step tracking line for tool execution."""
    sys.stdout.write(f"\033[90m  -> [{tool_name}] {detail}\033[0m\n")
    sys.stdout.flush()


def execute_tool(tool_name: str, params: dict, cwd: str) -> str:
    """Execute a tool and return the result as a string."""
    handlers = {
        "read_file": _read_file,
        "write_file": _write_file,
        "edit_file": _edit_file,
        "run_command": _run_command,
        "ask_user": _ask_user,
        "list_directory": _list_directory,
        "search_files": _search_files,
        "search_content": _search_content,
        "update_config": _update_config,
    }

    handler = handlers.get(tool_name)
    if not handler:
        return f"[Error] Unknown tool: {tool_name}"

    try:
        return handler(params, cwd)
    except Exception as e:
        return f"[Error] {tool_name} failed: {e}"


def _resolve_path(relative_path: str, cwd: str) -> str:
    """Resolve a relative path against the working directory."""
    path = os.path.join(cwd, relative_path)
    abs_path = os.path.abspath(path)

    if not abs_path.startswith(os.path.abspath(cwd)):
        raise ValueError(f"Path '{relative_path}' escapes the project directory.")

    return abs_path


MAX_READ_LINES = 200


def _read_file(params: dict, cwd: str) -> str:
    path = _resolve_path(params["path"], cwd)
    offset = params.get("offset", 0)

    if not os.path.exists(path):
        _step("read_file", f"{params['path']} - not found")
        return f"[Error] File not found: {params['path']}"

    if not os.path.isfile(path):
        return f"[Error] Not a file: {params['path']}"

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    total_lines = len(all_lines)
    start = max(0, offset)
    end = start + MAX_READ_LINES
    chunk = all_lines[start:end]
    content = "".join(chunk)
    shown = len(chunk)

    truncated = total_lines > end
    range_info = f"lines {start + 1}-{start + shown} of {total_lines}"
    _step("read_file", f"{params['path']} ({range_info})")

    header = f"[Read {params['path']}] ({range_info})"
    if truncated:
        header += f"\n[WARNING: File has {total_lines} lines. Showing first {MAX_READ_LINES} from offset {start}. Use offset parameter to read more: {{\"offset\": {end}}}]"

    return f"{header}\n{content}"


def _write_file(params: dict, cwd: str) -> str:
    path = _resolve_path(params["path"], cwd)
    content = params["content"]

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    line_count = content.count("\n") + 1
    _step("write_file", f"{params['path']} ({line_count} lines written)")
    return f"[Wrote {params['path']}] ({line_count} lines)"


def _edit_file(params: dict, cwd: str) -> str:
    path = _resolve_path(params["path"], cwd)
    old_string = params["old_string"]
    new_string = params["new_string"]

    if not os.path.exists(path):
        _step("edit_file", f"{params['path']} - not found")
        return f"[Error] File not found: {params['path']}"

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    count = content.count(old_string)
    if count == 0:
        _step("edit_file", f"{params['path']} - string not found")
        return f"[Error] String not found in {params['path']}"

    if count > 1:
        _step("edit_file", f"{params['path']} - {count} matches (ambiguous)")
        return f"[Error] String found {count} times in {params['path']}. Provide more context to make it unique."

    new_content = content.replace(old_string, new_string, 1)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)

    _step("edit_file", f"{params['path']} (1 replacement)")
    return f"[Edited {params['path']}] Replaced 1 occurrence."


def _run_command(params: dict, cwd: str) -> str:
    command = params["command"]
    _step("run_command", command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr

        if not output.strip():
            output = "(no output)"

        exit_code = result.returncode
        status = "ok" if exit_code == 0 else f"exit {exit_code}"
        _step("run_command", f"completed ({status})")
        return f"[Exit code: {exit_code}]\n{output.strip()}"

    except subprocess.TimeoutExpired:
        _step("run_command", "timed out (30s)")
        return "[Error] Command timed out after 30 seconds."


def _ask_user(params: dict, cwd: str) -> str:
    _step("ask_user", "waiting for developer input...")
    result = ask_user(params)
    _step("ask_user", result)
    return result


# --- Navigation tools ---

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".eggs", ".mypy_cache", ".pytest_cache",
    ".next", ".nuxt", "coverage", ".tox", ".orangutan-config",
}


def _list_directory(params: dict, cwd: str) -> str:
    target = params.get("path", ".")
    path = _resolve_path(target, cwd)

    if not os.path.exists(path):
        _step("list_directory", f"{target} - not found")
        return f"[Error] Directory not found: {target}"

    if not os.path.isdir(path):
        _step("list_directory", f"{target} - not a directory")
        return f"[Error] Not a directory: {target}"

    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return f"[Error] Permission denied: {target}"

    dirs = []
    files = []
    for entry in entries:
        full = os.path.join(path, entry)
        if os.path.isdir(full):
            if entry not in IGNORE_DIRS:
                dirs.append(f"  {entry}/")
        else:
            size = os.path.getsize(full)
            files.append(f"  {entry} ({_human_size(size)})")

    total = len(dirs) + len(files)
    _step("list_directory", f"{target} ({total} entries)")

    output = f"[Directory: {target}] ({len(dirs)} dirs, {len(files)} files)\n"
    output += "\n".join(dirs + files)
    return output


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def _search_files(params: dict, cwd: str) -> str:
    pattern = params.get("pattern", "*")
    _step("search_files", f"pattern: {pattern}")

    matches = []
    for root, dirs, files in os.walk(cwd):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                rel = os.path.relpath(os.path.join(root, filename), cwd)
                matches.append(rel.replace("\\", "/"))

                if len(matches) >= 50:
                    break
        if len(matches) >= 50:
            break

    _step("search_files", f"{len(matches)} files found")

    if not matches:
        return f"[search_files] No files matching '{pattern}'"

    output = f"[search_files] {len(matches)} files matching '{pattern}':\n"
    output += "\n".join(f"  {m}" for m in matches)
    if len(matches) >= 50:
        output += "\n  ... (truncated at 50 results)"
    return output


def _search_content(params: dict, cwd: str) -> str:
    pattern = params.get("pattern", "")
    glob_filter = params.get("glob", "*")

    if not pattern:
        return "[Error] search_content requires a 'pattern' parameter."

    _step("search_content", f"'{pattern}' in {glob_filter}")

    matches = []
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            if not fnmatch.fnmatch(filename, glob_filter):
                continue

            filepath = os.path.join(root, filename)
            rel = os.path.relpath(filepath, cwd).replace("\\", "/")

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            matches.append(f"  {rel}:{line_num}: {line.rstrip()[:120]}")

                            if len(matches) >= 50:
                                break
            except (PermissionError, IsADirectoryError, OSError):
                continue

            if len(matches) >= 50:
                break
        if len(matches) >= 50:
            break

    _step("search_content", f"{len(matches)} matches found")

    if not matches:
        return f"[search_content] No matches for '{pattern}' in {glob_filter}"

    output = f"[search_content] {len(matches)} matches for '{pattern}':\n"
    output += "\n".join(matches)
    if len(matches) >= 50:
        output += "\n  ... (truncated at 50 results)"
    return output


# --- Config tool ---

def _update_config(params: dict, cwd: str) -> str:
    """Update a specific section of orangutan.md or append new content."""
    section = params.get("section", "")
    content = params.get("content", "")

    if not section or not content:
        return "[Error] update_config requires 'section' and 'content' parameters."

    current = read_config(cwd)

    if not current:
        return "[Error] No orangutan.md found. Cannot update."

    # Try to find and replace the section
    section_header = f"## {section}"
    if section_header in current:
        # Find the section and replace its content (up to next ## header)
        start = current.index(section_header)
        after_header = start + len(section_header)

        # Find next section header or end of file
        next_section = current.find("\n## ", after_header)
        if next_section == -1:
            end = len(current)
        else:
            end = next_section

        updated = current[:after_header] + "\n" + content + "\n" + current[end:]
    else:
        # Append new section before "## Notes" if it exists, otherwise at end
        notes_pos = current.find("## Notes")
        if notes_pos != -1:
            updated = current[:notes_pos] + section_header + "\n" + content + "\n\n" + current[notes_pos:]
        else:
            updated = current.rstrip() + "\n\n" + section_header + "\n" + content + "\n"

    write_config(cwd, updated)
    _step("update_config", f"section '{section}' updated in orangutan.md")
    return f"[Updated orangutan.md] Section '{section}' updated."
