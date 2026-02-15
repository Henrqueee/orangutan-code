"""Config file management - orangutan.md detection, generation, and reading."""

import os

CONFIG_DIR = ".orangutan-config"
CONFIG_FILE = "orangutan.md"

# Files to scan when auto-generating config
KEY_FILES = [
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Gemfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    "Makefile",
    "README.md",
    "README.rst",
    ".env.example",
    ".env.sample",
    "tsconfig.json",
    ".eslintrc.json",
    ".eslintrc.js",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.ts",
    "webpack.config.js",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
]

TEMPLATE = """# Orangutan Code — Project Configuration
# This file is read by Orangutan Code on every session startup.
# The model uses it as context before any interaction.
# You can edit this file to guide the assistant's behavior.

## Project Overview
{overview}

## Tech Stack
{stack}

## Project Structure
```
{tree}
```

## Key Files Detected
{key_files}

## Development Setup
{setup}

## Conventions & Preferences
<!-- Add your preferences here. Examples: -->
<!-- - Code style: use single quotes, 2-space indent -->
<!-- - Language: always respond in English -->
<!-- - Commits: use conventional commits format -->
<!-- - Testing: always run tests before committing -->

## Notes
<!-- Add any notes the assistant should know about this project -->
"""


def config_path(cwd: str) -> str:
    """Return the full path to orangutan.md."""
    return os.path.join(cwd, CONFIG_DIR, CONFIG_FILE)


def config_exists(cwd: str) -> bool:
    """Check if orangutan.md exists in the project."""
    return os.path.isfile(config_path(cwd))


def read_config(cwd: str) -> str:
    """Read and return the contents of orangutan.md."""
    path = config_path(cwd)
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_config(cwd: str, content: str) -> str:
    """Write content to orangutan.md. Creates the directory if needed."""
    dir_path = os.path.join(cwd, CONFIG_DIR)
    os.makedirs(dir_path, exist_ok=True)
    path = config_path(cwd)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return path


def detect_key_files(cwd: str) -> list[str]:
    """Find which key files exist in the project root."""
    found = []
    for filename in KEY_FILES:
        if os.path.isfile(os.path.join(cwd, filename)):
            found.append(filename)
    return found


def read_key_file_summary(cwd: str, filename: str, max_lines: int = 30) -> str:
    """Read a key file and return a truncated summary."""
    path = os.path.join(cwd, filename)
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        content = "".join(lines[:max_lines])
        if len(lines) > max_lines:
            content += f"\n... ({len(lines) - max_lines} more lines)"
        return content
    except (PermissionError, OSError):
        return ""


def build_auto_config(cwd: str, tree: str) -> str:
    """Build an auto-generated orangutan.md from project analysis."""
    found_files = detect_key_files(cwd)

    # Detect stack from key files
    stack_items = []
    overview_parts = []
    setup_parts = []

    for filename in found_files:
        content = read_key_file_summary(cwd, filename)

        if filename == "package.json":
            stack_items.append("- Node.js / JavaScript/TypeScript")
            setup_parts.append("- `npm install` to install dependencies")
            setup_parts.append("- Check `package.json` scripts for available commands")
        elif filename == "pyproject.toml":
            stack_items.append("- Python")
            setup_parts.append("- `pip install -e .` or `pip install -r requirements.txt`")
        elif filename == "Cargo.toml":
            stack_items.append("- Rust")
            setup_parts.append("- `cargo build` to compile")
        elif filename == "go.mod":
            stack_items.append("- Go")
            setup_parts.append("- `go build` to compile")
        elif filename in ("docker-compose.yml", "docker-compose.yaml"):
            stack_items.append("- Docker / Docker Compose")
            setup_parts.append("- `docker-compose up -d` to start containers")
        elif filename == "Dockerfile":
            if "Docker" not in str(stack_items):
                stack_items.append("- Docker")
        elif filename == "requirements.txt":
            if "Python" not in str(stack_items):
                stack_items.append("- Python")
                setup_parts.append("- `pip install -r requirements.txt`")
        elif filename in ("tsconfig.json",):
            if "TypeScript" not in str(stack_items):
                stack_items.append("- TypeScript")
        elif filename in ("vite.config.ts", "vite.config.js"):
            stack_items.append("- Vite (frontend bundler)")
        elif filename in ("next.config.js", "next.config.ts"):
            stack_items.append("- Next.js")

    # Build overview from README if available
    if "README.md" in found_files:
        readme = read_key_file_summary(cwd, "README.md", max_lines=15)
        overview_parts.append(readme)

    overview = "\n".join(overview_parts) if overview_parts else "<!-- Add a brief project description here -->"
    stack = "\n".join(stack_items) if stack_items else "<!-- Add your tech stack here -->"
    key_files_str = "\n".join(f"- `{f}`" for f in found_files) if found_files else "- No common config files detected"
    setup = "\n".join(setup_parts) if setup_parts else "<!-- Add setup instructions here -->"

    return TEMPLATE.format(
        overview=overview,
        stack=stack,
        tree=tree,
        key_files=key_files_str,
        setup=setup,
    )
