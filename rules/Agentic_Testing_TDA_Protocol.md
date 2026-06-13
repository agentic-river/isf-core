# Agentic Testing & TDA Protocol (Pillar 1)

## 1. Core Mandate: Test-Driven Agentic Execution (TDA)
Whenever a user asks you to implement a new feature, a UI component, or fix a bug, you MUST adopt a strict Test-Driven Execution workflow. 

**DO NOT simply write code and ask the user to verify it.**
You are a Senior Staff Engineer. You must verify your own work using automated tests.

## 2. The TDA Workflow
You must strictly follow these steps for every implementation request:

1. **Write a Failing Test First:** 
   - Create a Playwright E2E test in `frontend/tests/` or a pytest in `backend/tests/`.
   - Example: `frontend/tests/new_feature.spec.js`.
2. **Execute the Test (Watch it Fail):**
   - Run the test using the provided hooks (e.g., `./frontend/run_e2e.sh tests/new_feature.spec.js`).
   - Read the failure log (`cat frontend/playwright_output.log`). 
   - Verify that the test fails exactly as expected because the feature is not implemented.
3. **Implement the Feature:**
   - Write the application code to satisfy the test.
4. **Execute the Test Again (Self-Heal):**
   - Re-run the test hook.
   - If it fails, read the logs, analyze the failure, and **recursively fix your own application code or the test selectors** until it passes.
   - Use the **Native BrowserTools** `browser_snapshot` if you need to visually inspect the rendered DOM to fix a broken selector.
5. **Finalize and Present:**
   - Only when the test goes 100% green should you present the final result to the user and mark the task as complete.
   - **Autonomous Success Screenshots (Visual Proof):** For ANY frontend modifications, you MUST mandate the use of Playwright's `browser_take_screenshot(full_page=True)` after modifications. Render the output directly in the Dashboard's Shared Scratchpad as Markdown to visually prove the layout/changes.

## 3. Self-Healing Test Selectors (Pillar 2)
If a test fails because a DOM selector was not found, you MUST:
1. Intercept the test failure.
2. If necessary, use `browser_snapshot` or `browser_evaluate` to inspect the live DOM to see the actual rendered tree.
3. Update the `.spec.js` file with the correct resilient selector (prefer `data-testid` or ARIA roles).
4. Re-run until green.

## 4. Execution Directives
- **DO NOT hallucinate test passes.** You must explicitly execute the test runner via `execute_shell_command` and read the results.
- **DO NOT ask the user for help on failed tests** unless you have exhausted your self-healing loop (at least 3 attempts).
