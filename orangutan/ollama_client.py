"""Ollama SDK integration - streaming chat with tool call parsing and model options."""

import json
import re
import sys
import threading
import time

from ollama import Client

MODEL = "qwen2.5-coder:7b-instruct"
TOOL_PATTERN = re.compile(r"<tool>\s*(\{.*?\})\s*</tool>", re.DOTALL)

# Ollama generation options for consistent, technical output.
# Reference: https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
MODEL_OPTIONS = {
    "temperature": 0.4,          # Lower = more focused and deterministic output
    "top_p": 0.9,                # Nucleus sampling: keeps top 90% probability mass
    "top_k": 40,                 # Limits token pool per step
    "num_ctx": 8192,             # Context window size (tokens)
    "num_predict": -1,           # No limit on response length (-1 = unlimited)
    "repeat_penalty": 1.1,       # Penalizes repeated tokens/phrases
    "stop": ["[END]"],           # Custom stop sequence for report boundary
}

# Thinking indicator
THINKING_FRAMES = [".", "..", "..."]


class _ThinkingIndicator:
    """Shows a 'Thinking...' status while waiting for the first token."""

    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        # Clear the thinking line
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _animate(self):
        idx = 0
        while self._running:
            frame = THINKING_FRAMES[idx % len(THINKING_FRAMES)]
            sys.stdout.write(f"\r\033[90m  Thinking{frame}\033[0m")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.5)


class OllamaChat:
    def __init__(self, system_prompt: str, options: dict | None = None):
        self.client = Client()
        self.options = options or MODEL_OPTIONS
        self.messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]

    def send(self, user_message: str) -> str:
        """Send a user message and stream the response. Returns full response text."""
        self.messages.append({"role": "user", "content": user_message})

        full_response = ""
        indicator = _ThinkingIndicator()
        indicator.start()
        first_token = True

        try:
            stream = self.client.chat(
                model=MODEL,
                messages=self.messages,
                stream=True,
                options=self.options,
                keep_alive="10m",
            )

            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    if first_token:
                        indicator.stop()
                        first_token = False
                    full_response += token
                    sys.stdout.write(token)
                    sys.stdout.flush()

        except Exception as e:
            indicator.stop()
            error_msg = f"\n[Connection error: {e}]"
            sys.stdout.write(error_msg)
            sys.stdout.flush()
            full_response += error_msg

        if first_token:
            indicator.stop()

        self.messages.append({"role": "assistant", "content": full_response})

        sys.stdout.write("\n")
        sys.stdout.flush()

        return full_response

    def add_tool_result(self, result: str) -> None:
        """Add a tool result to the conversation as a user message."""
        self.messages.append({"role": "user", "content": result})


def parse_tool_calls(response: str) -> list[dict]:
    """Extract tool calls from the model's response."""
    tool_calls = []

    for match in TOOL_PATTERN.finditer(response):
        try:
            parsed = json.loads(match.group(1))
            tool_name = parsed.get("tool")
            params = parsed.get("params", {})
            if tool_name:
                tool_calls.append({"tool": tool_name, "params": params})
        except json.JSONDecodeError:
            continue

    return tool_calls
