"""CLI entry point - Click-based REPL for Orangutan Code."""

import os
import sys

import click

from orangutan import __version__
from orangutan.ollama_client import OllamaChat, parse_tool_calls
from orangutan.report import contains_report, format_report
from orangutan.system_prompt import build_system_prompt
from orangutan.tools import execute_tool

BANNER = rf"""
   ___                            _
  / _ \ _ __ __ _ _ __   __ _ _  _| |_ __ _ _ __
 | | | | '__/ _` | '_ \ / _` | | | | __/ _` | '_ \
 | |_| | | | (_| | | | | (_| | |_| | || (_| | | | |
  \___/|_|  \__,_|_| |_|\__, |\__,_|\__\__,_|_| |_|
                         |___/
  Orangutan Code v{__version__} — AI Coding Assistant
  Model: qwen2.5-coder:7b-instruct (local via Ollama)
  Type /help for commands, /exit to quit.
"""

HELP_TEXT = """
Commands:
  /help     Show this help message
  /exit     Exit Orangutan Code
  /clear    Clear conversation history
  /tree     Show project directory tree
"""

MAX_TOOL_ROUNDS = 10

REPORT_START = "--- EXECUTION REPORT ---"
REPORT_END = "--- END REPORT ---"


def _reprint_colored_report(response: str) -> None:
    """Clear the plain-text report from the terminal and reprint it with ANSI colors.

    The streaming output already printed the report without colors.
    This function moves the cursor up, clears those lines, and reprints
    the report section with colored file/function references.
    """
    start_idx = response.find(REPORT_START)
    end_idx = response.find(REPORT_END)
    if start_idx == -1 or end_idx == -1:
        return

    report_section = response[start_idx : end_idx + len(REPORT_END)]
    plain_lines = report_section.split("\n")
    num_lines = len(plain_lines)

    # Move cursor up and clear each plain-text report line
    sys.stdout.write(f"\033[{num_lines}A")
    for _ in range(num_lines):
        sys.stdout.write("\033[2K\033[1B")
    sys.stdout.write(f"\033[{num_lines}A")

    # Print the colored version
    colored = format_report(response)
    colored_start = colored.find("\033")  # find first ANSI sequence in report area
    # Re-extract just the report portion from the colored output
    c_start = colored.find(REPORT_START)
    # Find the visible end (after ANSI codes around REPORT_END)
    c_end = colored.find(REPORT_END, c_start)
    # Walk forward past the REPORT_END text and any trailing ANSI reset
    c_end_full = colored.find("\n", c_end)
    if c_end_full == -1:
        c_end_full = len(colored)

    # Find the actual colored block start (includes ANSI prefix)
    # Walk backwards from c_start to capture leading ANSI codes
    search_pos = c_start
    while search_pos > 0 and colored[search_pos - 1] != "\n":
        search_pos -= 1

    colored_report = colored[search_pos:c_end_full]
    sys.stdout.write(colored_report + "\n")
    sys.stdout.flush()


@click.command()
@click.option(
    "--path",
    "-p",
    default=".",
    help="Project directory to work in.",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
def main(path: str) -> None:
    """Orangutan Code — AI-powered coding assistant using local LLMs."""
    cwd = os.path.abspath(path)

    click.echo(BANNER)
    click.echo(f"  Working directory: {cwd}\n")

    system_prompt = build_system_prompt(cwd)
    chat = OllamaChat(system_prompt)

    while True:
        try:
            user_input = input("\033[38;5;208m>\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            click.echo("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd in ("/exit", "/quit"):
                click.echo("Goodbye!")
                sys.exit(0)
            elif cmd == "/help":
                click.echo(HELP_TEXT)
                continue
            elif cmd == "/clear":
                system_prompt = build_system_prompt(cwd)
                chat = OllamaChat(system_prompt)
                click.echo("  Conversation cleared.\n")
                continue
            elif cmd == "/tree":
                from orangutan.context import build_directory_tree
                click.echo(build_directory_tree(cwd))
                click.echo()
                continue
            else:
                click.echo(f"  Unknown command: {user_input}\n")
                continue

        click.echo()

        # Send to LLM and stream response
        response = chat.send(user_input)

        # Agentic tool loop: execute tools and feed results back
        for _ in range(MAX_TOOL_ROUNDS):
            tool_calls = parse_tool_calls(response)

            if not tool_calls:
                break

            results = []
            for tc in tool_calls:
                result = execute_tool(tc["tool"], tc["params"], cwd)
                results.append(f"Tool result for {tc['tool']}:\n{result}")

            combined = "\n\n".join(results)
            chat.add_tool_result(combined)

            click.echo()
            response = chat.send("Continue based on the tool results above.")

        # Re-print the execution report with colors if present
        if contains_report(response):
            _reprint_colored_report(response)

        click.echo()
