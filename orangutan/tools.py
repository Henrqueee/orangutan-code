"""Tool execution engine - handles read, write, edit, bash, and ask_user operations."""

import os
import subprocess
import sys

from orangutan.ask_tool import ask_user


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


def _read_file(params: dict, cwd: str) -> str:
    path = _resolve_path(params["path"], cwd)

    if not os.path.exists(path):
        _step("read_file", f"{params['path']} - not found")
        return f"[Error] File not found: {params['path']}"

    if not os.path.isfile(path):
        return f"[Error] Not a file: {params['path']}"

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    line_count = content.count("\n") + 1
    _step("read_file", f"{params['path']} ({line_count} lines)")
    return f"[Read {params['path']}] ({line_count} lines)\n{content}"


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
