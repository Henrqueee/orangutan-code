# Orangutan Code — Setup Guide

## Prerequisites

1. **Python 3.12+** installed and in PATH
2. **Ollama** installed and running (`ollama serve`)
3. **Model pulled**: `ollama pull qwen2.5-coder:7b-instruct`

## Installation

```bash
cd orangutan-code
pip install -e .
```

This installs the `orangutan` command globally.

### PATH Setup (Windows)

If you get "orangutan is not recognized", add the Python Scripts directory to PATH:

```
C:\Users\<your-user>\AppData\Roaming\Python\Python312\Scripts
```

### PATH Setup (Git Bash / MINGW64)

Add to your `~/.bashrc`:

```bash
export PATH="$PATH:/c/Python312:/c/Python312/Scripts:/c/Users/<your-user>/AppData/Roaming/Python/Python312/Scripts"
```

Then reload: `source ~/.bashrc`

## Usage

### Start in current directory
```bash
orangutan
```

### Start in a specific project
```bash
orangutan -p /path/to/project
```

### REPL Commands

| Command  | Description                    |
|----------|--------------------------------|
| `/help`  | Show available commands        |
| `/exit`  | Exit the assistant             |
| `/clear` | Clear conversation history     |
| `/tree`  | Show project directory tree    |

## UX Features

### Thinking Indicator
When the model is processing, a `Thinking...` animation appears until the
first token arrives.

### Step Tracking
Every tool execution prints a status line:
```
  -> [read_file] src/main.py (45 lines)
  -> [run_command] npm test
  -> [run_command] completed (ok)
  -> [ask_user] waiting for developer input...
```

### Execution Report
After completing a task, the assistant generates a structured execution report
with colored references:
- **Cyan**: file paths (e.g., `src/models/user.py`)
- **Yellow**: function/class names (e.g., `validate_input()`)
- **Green**: report delimiters
- **Dim**: section headers

The report includes: actions performed, files modified/created/read,
commands executed, and a technical summary referencing specific code paths.

### Developer Decision Prompts (ask_user)
The assistant uses interactive prompts to consult you on every decision:
```
? Which database should we use?
> PostgreSQL
  SQLite
  MongoDB
  Other (type custom answer)
```

Navigate with arrow keys, press Enter to select. You can always choose
"Other" to type a custom answer.

See [ask-tool.md](ask-tool.md) for full details.

## Development

Since it's installed in editable mode (`-e`), changes to the source files
take effect immediately — no reinstall needed (unless you add new
dependencies to `pyproject.toml`).

## Documentation

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | System architecture and how it works |
| [philosophy.md](philosophy.md) | Core philosophy: developer-driven development |
| [ask-tool.md](ask-tool.md) | ask_user tool reference and usage guide |
| [ollama-options.md](ollama-options.md) | Ollama model parameters reference and tuning guide |
