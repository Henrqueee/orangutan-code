# ask_user Tool — Reference

## Overview

`ask_user` is the primary interaction tool in Orangutan Code. It presents
questions to the developer with selectable options and an optional free-text
input. The assistant MUST use this tool for every decision that affects the
project.

## Tool Signature

```json
{
  "tool": "ask_user",
  "params": {
    "question": "Your question here",
    "options": ["Option A", "Option B", "Option C"]
  }
}
```

### Parameters

| Parameter  | Type       | Required | Description                                |
|------------|------------|----------|--------------------------------------------|
| `question` | `string`   | Yes      | The question to present to the developer   |
| `options`  | `string[]` | No       | List of selectable choices (ALWAYS 3)      |

### The 3-Option Rule

The model MUST always provide **exactly 3 options**. The CLI automatically
appends a 4th option: "Other (type custom answer)" for free-text input.

The developer sees 4 choices total:
1. Option A (arrow-key selectable)
2. Option B (arrow-key selectable)
3. Option C (arrow-key selectable)
4. Other (type custom answer) ← added automatically by the CLI

Only omit `options` for simple factual questions where predefined choices
don't make sense (e.g., "What should the table name be?").

## UX Behavior

### With Options
```
? Which database should we use for this project?
> PostgreSQL
  SQLite
  MongoDB
  Other (type custom answer)
```

The developer navigates with arrow keys and presses Enter to select.
If "Other" is selected, a text input field appears.

### Without Options (Free Text)
```
? What should the API endpoint path be?
> _
```

The developer types their answer directly.

## Return Values

| Scenario              | Return Value                        |
|-----------------------|-------------------------------------|
| Option selected       | `[User answer] PostgreSQL`          |
| Custom text entered   | `[User answer] MariaDB with Redis`  |
| Developer cancels     | `[User cancelled the prompt]`       |

## When To Use

### ALWAYS use ask_user for:

**Object & Schema Decisions**
- "What fields should the User model have?"
- "Should the ID be UUID or auto-increment?"
- "What type should the `status` field be?"

**Workflow Decisions**
- "How should the authentication flow work?"
- "Should we validate input before or after transformation?"
- "What should happen when this API call fails?"

**Architecture Decisions**
- "Should we use a service layer or call the repository directly?"
- "How should these modules communicate?"
- "Where should this logic live?"

**Implementation Decisions**
- "Which HTTP client library should we use?"
- "Should this be a class or a function?"
- "How should we handle this edge case?"

**Confirmation Before Action**
- "I'm about to create src/models/user.py with these fields. Proceed?"
- "I'll run `npm install express`. Is that ok?"
- "I want to modify the database schema. Here's the plan..."

## Mid-Flow Questioning

The `ask_user` tool can be called at **any point during execution**, not just
at the start. The agentic tool loop in `cli.py` supports this: each tool call
(including `ask_user`) is executed, the result is fed back to the model, and
the model continues based on the developer's answer.

### How it works

1. Developer requests a task
2. Model starts working (reading files, analyzing code...)
3. A decision point or doubt arises mid-execution
4. Model **pauses** and calls `ask_user` with 3 options
5. Developer selects an option or types a custom answer
6. Model receives the answer and continues execution
7. If another question arises → repeat from step 4

This ensures the developer is in control at every step, even during complex
multi-step tasks. The model never makes assumptions — it always asks.

## Design Philosophy

The `ask_user` tool exists because Orangutan Code operates on the principle
that **the developer is the architect**. The AI is a tool that executes the
developer's vision — it does not impose its own.

Every question asked is an opportunity for the developer to:
- Shape the codebase according to their vision
- Understand what is being done and why
- Catch mistakes before they happen
- Learn and make informed decisions

The assistant should never feel hesitant about using `ask_user`. More
questions are always better than wrong assumptions.

## Implementation

- **Library**: `questionary` (built on `prompt_toolkit`)
- **Source**: `orangutan/ask_tool.py`
- **Registered in**: `orangutan/tools.py`
- **Instructed in**: `orangutan/system_prompt.py`
