"""ask_user tool - Interactive prompts for the developer to make decisions."""

import questionary
from questionary import Style

STYLE = Style([
    ("qmark", "fg:orange bold"),
    ("question", "bold"),
    ("answer", "fg:orange bold"),
    ("pointer", "fg:orange bold"),
    ("highlighted", "fg:orange bold"),
    ("selected", "fg:orange"),
    ("instruction", "fg:gray"),
])


def ask_user(params: dict) -> str:
    """Present a question to the user with options and/or free text input.

    params:
        question: str - The question to ask
        options: list[str] (optional) - Choices for the user to pick from
    """
    question_text = params.get("question", "")
    options = params.get("options", [])

    if not question_text:
        return "[Error] ask_user requires a 'question' parameter."

    print()

    if options:
        # Add a custom input option at the end
        choices = list(options) + ["Other (type custom answer)"]

        answer = questionary.select(
            question_text,
            choices=choices,
            style=STYLE,
            instruction="(Use arrow keys to select)",
        ).ask()

        if answer is None:
            return "[User cancelled the prompt]"

        if answer == "Other (type custom answer)":
            custom = questionary.text(
                "Your answer:",
                style=STYLE,
            ).ask()

            if custom is None:
                return "[User cancelled the prompt]"

            return f"[User answer] {custom}"

        return f"[User answer] {answer}"

    else:
        # No options provided, just free text input
        answer = questionary.text(
            question_text,
            style=STYLE,
        ).ask()

        if answer is None:
            return "[User cancelled the prompt]"

        return f"[User answer] {answer}"
