# 🤖 AI Rule Management & Creation Guide

This document defines the strict protocol for how AI agents must handle, create, and modify project rules and guidelines within this repository.

## 1. Rule Storage Location
**CRITICAL:** All rules, guidelines, and AI behavior instructions MUST be saved in the `rules/` directory at the root of the project. 

*   🟢 **Correct:** `rules/API_Conventions_Guide.md`
*   🔴 **Incorrect:** `docs/API_Conventions.md`
*   🔴 **Incorrect:** `API_Conventions.md` (Root directory)

If a user asks you to "add a rule", "create a guideline", or "save these instructions", you MUST automatically target the `rules/` directory. If the directory does not exist, you must create it.

## 2. File Naming Conventions
*   Rule files must be written in **Markdown** format (`.md`).
*   Filenames should be descriptive, concise, and use`PascalCase` with underscores (e.g., `Github_MCP_Guide.md` or `Context7_Guide.md`).
*   Always include `guide`, `rules`, or `protocol` in the filename to indicate its purpose.

## 3. Rule Structure Requirements
Every new rule file created by an AI agent must include:
1.  **H1 Title:** Clearly stating the topic of the rule.
2.  **Objective/Summary:** A brief sentence explaining *why* this rule exists and *when* it applies.
3.  **Actionable Directives:** Use strong verbs (e.g., "MUST", "NEVER", "ALWAYS"). Bullet points or numbered lists are highly encouraged for readability.
4.  **Examples:** Where applicable, provide a 🟢 **Good** and 🔴 **Bad** example to eliminate ambiguity.

## 4. Modifying Existing Rules
Before creating a new rule, use codebase search tools to verify if a similar rule already exists in the `rules/` folder.
*   If a rule for the topic exists: **Update** the existing file using the `smart_replace` or `write_file_content` tools.
*   Do not create duplicate rules (e.g., do not create `testing_rules.md` if `Playwright_E2E_Testing_Guide.md` already exists).