# Playwright E2E Testing Guide for AI Agents

## Objective
This document outlines the architecture, setup, and execution strategy for End-to-End (E2E) testing using Playwright. It defines strict rules for running, writing, and debugging tests autonomously.

## 1. Core Principles
- **Container Execution:** You MUST run tests inside the container using the provided shell script to avoid timeouts.
- **No Test Mutilation:** You MUST NEVER blindly modify a failing test just to make it pass if the application codebase is the true source of the bug. Fix the application, not the test.
- **Real Database Interaction:** You MUST NOT mock network requests for internal APIs. 

## 2. Execution Strategy

### How to Run Tests
1. **Trigger the test script:**
   Pass the path to the test file (relative to the `frontend/` directory).
   ```bash
   ./run_e2e.sh tests/agent_ledger.spec.js
   ```
2. **Read the results:**
   ```bash
   cat frontend/playwright_output.log
   ```

## 3. Examples

### 🟢 Good Example
*   **Good:** Using dynamic, state-independent selectors such as `page.getByPlaceholder(/Type a message/i)`.
*   **Good:** Running `./frontend/run_e2e.sh tests/my_test.spec.js` and analyzing the `playwright_output.log` file.

### 🔴 Bad Example
*   **Bad:** Executing `npx playwright test` directly via shell, which will cause an AI timeout error.
*   **Bad:** Using rigid CSS classes `page.locator('textarea[placeholder="Type a message..."]')` which break when UI translations or states change.