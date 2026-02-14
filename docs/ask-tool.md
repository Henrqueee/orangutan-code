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
| `options`  | `string[]` | No       | List of selectable choices                 |

- When `options` is provided: arrow-key selection menu + "Other" for custom input
- When `options` is omitted: free-text input field

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
