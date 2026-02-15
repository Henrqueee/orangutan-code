"""Execution report formatter - colorizes file/function references in the report."""

import re
import sys

# ANSI color codes
CYAN = "\033[36m"       # File paths
YELLOW = "\033[33m"     # Function/class names
GREEN = "\033[32m"      # Report delimiters
DIM = "\033[90m"        # Section headers (##)
RESET = "\033[0m"
BOLD = "\033[1m"

# Pattern to find <<references>> markers in the report
REF_PATTERN = re.compile(r"<<(.+?)>>")

# Report boundary markers
REPORT_START = "--- EXECUTION REPORT ---"
REPORT_END = "--- END REPORT ---"


def contains_report(text: str) -> bool:
    """Check if the response contains an execution report."""
    return REPORT_START in text and REPORT_END in text


def format_report(text: str) -> str:
    """Extract and colorize the execution report from the response.

    Replaces <<file_path>> and <<function()>> markers with colored ANSI output:
    - File paths (containing / or .) → cyan
    - Function/class names → yellow
    - Report delimiters → green bold
    - Section headers (##) → dim
    """
    start_idx = text.find(REPORT_START)
    end_idx = text.find(REPORT_END)

    if start_idx == -1 or end_idx == -1:
        return text

    before_report = text[:start_idx]
    report_block = text[start_idx:end_idx + len(REPORT_END)]
    after_report = text[end_idx + len(REPORT_END):]

    # Colorize the report
    colored = _colorize_report(report_block)

    return before_report + colored + after_report


def _colorize_report(report: str) -> str:
    """Apply ANSI colors to report elements."""
    lines = report.split("\n")
    result = []

    for line in lines:
        # Colorize report delimiters
        if REPORT_START in line or REPORT_END in line:
            result.append(f"{GREEN}{BOLD}{line}{RESET}")
            continue

        # Colorize section headers (## ...)
        stripped = line.lstrip()
        if stripped.startswith("## "):
            result.append(f"{DIM}{BOLD}{line}{RESET}")
            continue

        # Colorize <<references>>
        colored_line = REF_PATTERN.sub(_colorize_ref, line)
        result.append(colored_line)

    return "\n".join(result)


def _colorize_ref(match: re.Match) -> str:
    """Colorize a single <<reference>> based on its content."""
    ref = match.group(1)

    # File paths contain / or . (e.g., src/main.py)
    if "/" in ref or "." in ref:
        return f"{CYAN}{BOLD}{ref}{RESET}"

    # Function/class names (e.g., validate_input(), UserModel)
    return f"{YELLOW}{BOLD}{ref}{RESET}"


def print_report(text: str) -> None:
    """Print the full response, colorizing the report section if present."""
    if contains_report(text):
        formatted = format_report(text)
        sys.stdout.write(formatted)
    else:
        sys.stdout.write(text)
    sys.stdout.flush()
