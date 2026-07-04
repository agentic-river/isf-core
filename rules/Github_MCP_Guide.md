# GitHub MCP Server Guide for AI Agents

## Objective
This document outlines the standard operating procedures and mandatory guidelines for AI agents using the GitHub MCP Server tools in this repository.

## 1. Core Principles
- **Use MCP Tools:** You MUST always prefer the registered GitHub MCP tools (e.g., `create_pull_request`, `get_issue`, `push_files`) over executing raw `git` or `gh` CLI commands when interacting with the remote GitHub repository.
- **No Destructive Actions:** You NEVER close issues, delete branches, or merge pull requests (`merge_pull_request`) without explicit confirmation from the user.

## 2. Standard Workflows

### A. Pull Request (PR) Workflow
1. **Branching:** Use `create_branch` to branch off the default base branch.
2. **Committing:** Use `create_or_update_file` or `push_files`.
3. **Creating the PR:** Use `create_pull_request` with a comprehensive title and markdown body.

## 3. Examples

### 🟢 Good Example
*   **Good:** Using `search_code` to understand context, creating a branch via `create_branch`, committing changes with `push_files`, and opening a pull request with `create_pull_request`.

### 🔴 Bad Example
*   **Bad:** Running `git push origin main` in the terminal instead of using the `push_files` tool.
*   **Bad:** Calling `merge_pull_request` without the human user explicitly stating "You can merge this PR".