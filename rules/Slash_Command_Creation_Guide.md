# 🤖 Slash Command Creation Guide

## Objective
This document outlines the standard protocol for AI agents when tasked with creating or adding a new slash command (e.g., `/my-command <query>`) to the chat interface. Following this guide ensures the command is properly integrated into the UI autocomplete and correctly routed in the frontend logic.

## 1. Core Requirements

Whenever a user requests a new chat command, you MUST update the following two core files:

1.  **`frontend/src/constants.jsx` (UI Autocomplete)**
    *   You MUST add the new command to the exported `COMMANDS` array.
    *   This ensures the command appears in the dropdown menu when the user types `/` in the chat input.
    *   Include a relevant Lucide-React icon and a clear description.

2.  **`frontend/src/hooks/useCommandProcessor.js` (Command Execution)**
    *   You MUST add the parsing logic for the new command in the main `processCommand` function (or equivalent parsing block).
    *   Extract any arguments (e.g., `<query>`) provided after the command.
    *   Create a dedicated async handler function (e.g., `handleMyCommand`) to process the logic, stream responses, or make API calls to the backend.

## 2. Standard Workflow

1.  **Update `constants.jsx`:**
    Locate the `COMMANDS` array and append the new command object:
    ```javascript
    {
      command: "/my-command",
      description: "Description of what it does",
      icon: <IconComponent size={18} />
    }
    ```
2.  **Update `useCommandProcessor.js`:**
    *   Add the `if (text.startsWith("/my-command"))` block.
    *   Implement `const handleMyCommand = async (query) => { ... }`.
    *   If there is a `/help` switch or static help message block in the processor, update that as well.

## 3. Examples

### 🟢 Good Example
*   **Good:** Adding `{ command: "/browser-automation", description: "Run browser automation", icon: <Globe size={18} /> }` to `constants.jsx` AND creating `handleBrowserAutomation(query)` in `useCommandProcessor.js`.

### 🔴 Bad Example
*   **Bad:** Implementing the parsing logic in `useCommandProcessor.js` but forgetting to update `constants.jsx`. The user won't see the command when they type `/`.
*   **Bad:** Handling the command purely on the backend without adding the frontend UI and routing implementations.