# Orangutan Code — Architecture

## Overview

Orangutan Code is a **developer-driven** AI coding assistant that runs locally
via Ollama. The developer holds full control over every decision — the AI
proposes, asks, and executes only what the developer approves.

See [philosophy.md](philosophy.md) for the full design philosophy.

## Stack

- **Language**: Python 3.12
- **CLI framework**: Click
- **LLM backend**: Ollama (local) via `ollama-python` SDK
- **Model**: `qwen2.5-coder:7b-instruct`
- **Interactive prompts**: `questionary` (arrow-key selection + free text)

## Project Structure

```
orangutan-code/
├── orangutan/
│   ├── __init__.py          # Package init, version
│   ├── cli.py               # Click entry point, REPL loop, agentic tool loop, report rendering
│   ├── ollama_client.py     # Ollama SDK integration, streaming, model options, thinking indicator
│   ├── context.py           # Directory tree builder
│   ├── system_prompt.py     # System prompt with developer autonomy rules + execution report spec
│   ├── tools.py             # Tool execution engine with step tracking
│   ├── ask_tool.py          # ask_user tool (questionary-based interactive prompts)
│   └── report.py            # Execution report parser and ANSI colorizer
├── docs/
│   ├── architecture.md      # This file
│   ├── philosophy.md        # Core philosophy: developer-driven development
│   ├── ask-tool.md          # ask_user tool reference and usage guide
│   ├── ollama-options.md    # Ollama model parameters reference
│   └── setup.md             # Installation and usage instructions
└── pyproject.toml           # Package config, dependencies, entry point
```

## How It Works

### 1. Startup (`cli.py`)
- User runs `orangutan` (or `orangutan -p /path/to/project`)
- The CLI resolves the working directory
- `context.py` scans the directory tree (up to 4 levels deep)
- `system_prompt.py` builds a system prompt with:
  - Communication style rules (technical, objective, no filler)
  - Developer autonomy rules (the developer decides everything)
  - Tool definitions (including `ask_user` as the primary tool)
  - Execution report specification with `<<reference>>` markers
  - Anti-overengineering rules (only do what was requested)
  - Project directory tree as context
- An `OllamaChat` session is initialized with the system prompt and model options

### 2. REPL Loop (`cli.py`)
- User types a message
- Slash commands (`/help`, `/exit`, `/clear`, `/tree`) are handled locally
- Everything else is sent to the LLM via `OllamaChat.send()`

### 3. LLM Communication (`ollama_client.py`)
- A "Thinking..." indicator appears while waiting for the first token
- Messages are sent to Ollama's chat API with streaming enabled
- **Model options** are passed via the `options` parameter (see [ollama-options.md](ollama-options.md)):
  - `temperature: 0.4` — focused, deterministic output
  - `num_ctx: 8192` — expanded context window
  - `top_p: 0.9`, `top_k: 40` — balanced sampling
  - `repeat_penalty: 1.1` — prevents repetition
  - `num_predict: -1` — unlimited response length
- **`keep_alive: "10m"`** keeps the model loaded in memory for 10 minutes
- Tokens are printed in real-time as they arrive
- The full response is stored in conversation history

### 4. Agentic Tool Loop (`cli.py` + `tools.py`)
- The LLM uses `<tool>{"tool": "name", "params": {...}}</tool>` blocks
- `parse_tool_calls()` extracts these from the response via regex
- Each tool call is executed by `execute_tool()` in `tools.py`
- Step tracking prints status lines: `-> [tool_name] details`
- Results are fed back into the conversation
- The loop continues (up to 10 rounds) until the LLM responds without tools

### 5. Execution Report (`report.py` + `cli.py`)
- After the tool loop ends, the final response is checked for `--- EXECUTION REPORT ---`
- If present, `_reprint_colored_report()` in `cli.py`:
  - Moves the cursor up to overwrite the plain-text report
  - Reprints the report with ANSI colors applied by `report.py`
- `report.py` applies colors to:
  - `<<file/paths>>` → **cyan** (file references)
  - `<<function_names()>>` → **yellow** (function/class references)
  - Report delimiters → **green bold**
  - Section headers (`##`) → **dim bold**

### 6. Available Tools (`tools.py`)

| Tool | Description | Priority |
|------|-------------|----------|
| `ask_user` | Ask the developer a question with options or free text | **PRIMARY** |
| `read_file` | Read file contents. Path must be within project dir. | Standard |
| `write_file` | Write/create a file. Creates parent dirs if needed. | Standard |
| `edit_file` | Replace a unique string in a file (single occurrence). | Standard |
| `run_command` | Execute a shell command with 30s timeout. | Standard |

`ask_user` is the most important tool. See [ask-tool.md](ask-tool.md).

### 7. Developer Autonomy (System Prompt)

The system prompt enforces that:
- The developer makes ALL decisions about schemas, workflows, and architecture
- `ask_user` must be used before any action that affects the project
- The AI never assumes — it always asks
- Options are presented with concrete choices when possible
- The developer can always type a custom answer
- The AI NEVER over-engineers: it does only what was requested, nothing more
- When doubts or new needs arise, `ask_user` is used immediately

### 8. Anti-Overengineering Principle

The assistant is strictly prohibited from:
- Adding features, improvements, or refactors that were **not explicitly requested**
- Creating abstractions, helpers, or utilities beyond what the task requires
- Adding error handling, validation, or edge-case coverage for scenarios not specified
- Suggesting or implementing "nice to have" improvements
- Expanding scope beyond the developer's original request

When a new need or question emerges during execution, the assistant MUST use
`ask_user` to consult the developer instead of making assumptions.

### 9. Security
- All file paths are resolved and checked to stay within the project directory
- Shell commands run with a 30-second timeout
- No network access beyond localhost Ollama
- The developer must approve every action via `ask_user`
