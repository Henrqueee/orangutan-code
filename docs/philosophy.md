# Orangutan Code — Philosophy

## Core Principle: Developer-Driven Development

Orangutan Code is NOT an autonomous coding agent. It is a **developer-driven
assistant** where the human programmer holds full control over every decision
that shapes the project.

The AI does not decide. The AI proposes, asks, and executes what the developer
approves. Nothing more.

## Why This Matters

Traditional AI coding assistants tend to:
- Make assumptions about what the developer wants
- Choose architectures, patterns, and implementations autonomously
- Generate code without consulting the developer on trade-offs
- Produce bloated, over-engineered solutions

Orangutan Code rejects this model entirely. The developer is the architect,
the decision-maker, and the owner of every line of code.

## The ask_user Tool: The Heart of Orangutan Code

The `ask_user` tool is the most important tool in the system. It is not a
fallback — it is the **primary mechanism** through which the assistant operates.

### When ask_user MUST Be Used

The assistant must use `ask_user` before:

1. **Schemas & Data Structures**
   - Defining any object, class, or interface
   - Choosing field types, names, or relationships
   - Deciding between data modeling approaches

2. **Workflows & Logic**
   - Defining control flow or business logic
   - Choosing error handling strategies
   - Deciding execution order or pipeline structure

3. **Architecture & Patterns**
   - Choosing design patterns (MVC, repository, etc.)
   - Deciding module boundaries or separation of concerns
   - Selecting communication patterns between components

4. **Implementation Details**
   - Choosing libraries or dependencies
   - Deciding on naming conventions
   - Selecting between multiple valid implementations
   - Any code that could reasonably be written in more than one way

5. **File Operations**
   - Before creating, modifying, or deleting any file
   - Before running any shell command
   - Before making any change that affects the project state

6. **Ambiguity**
   - Whenever the request is not 100% clear
   - Whenever there are multiple valid interpretations
   - Whenever the developer might have a preference

### The Rule Is Simple

**If there is a choice to be made, the developer makes it.**

The assistant should use `ask_user` liberally — it is always better to ask
than to assume. The developer's time spent answering a question is always
worth more than the time spent undoing an unwanted change.

## How ask_user Works

The assistant calls `ask_user` with:
- A clear **question** describing the decision
- Concrete **options** when applicable (the developer can always type a custom answer)

Example flow:
```
Assistant: I need to create a User model. Let me ask about the structure.

  -> [ask_user] waiting for developer input...

  ? How should the User model be structured?
  > Name + Email + Password hash
    Name + Email + OAuth provider
    Minimal (just Email + ID)
    Other (type custom answer)

Developer selects option or types custom answer.

  -> [ask_user] [User answer] Name + Email + Password hash