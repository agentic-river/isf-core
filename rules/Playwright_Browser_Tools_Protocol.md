# Playwright Native Browser Tools Protocol

## Objective
This document defines the mandatory protocol for using the **Playwright MCP Server** ("Hand and Eye") system. This standalone Host OS service replaces legacy in-process/Docker browser automation and provides stable, direct control over browser navigation.

## 1. Core Principles
- **Host-Native Stability:** Use the `browser_*` tools exposed by the Playwright MCP Server (running natively on port `:8899`). This bypasses Docker networking restrictions, allowing both the AI Agent (in Docker) and the AI Daemon (on Host) to directly see `localhost`.
- **Auto-Healing:** The MCP server automatically handles missing browser binaries.
- **Snapshot-Driven Actions:** NEVER guess DOM selectors. You MUST use `browser_snapshot` to see the current page structure. Use the attributes found in the snapshot (ARIA roles, labels, or IDs) to construct stable selectors.
- **Visual Verification:** Use `browser_take_screenshot` to verify page state transitions. This is especially important for the user's "Live View" dashboard.

## 2. Tool Reference ("The Hand")
| Tool | Purpose |
| :--- | :--- |
| `browser_navigate` | Loads a URL. Always waits for `networkidle`. |
| `browser_snapshot` | Returns a textual summary of the DOM/Accessibility tree. **MANDATORY** before interaction. |
| `browser_click` | Clicks an element using a CSS selector or text-based locator. |
| `browser_type` | Types text into a field. Use for standard inputs. |
| `browser_fill_form` | Fills an input. More efficient than `type` for simple forms. |
| `browser_wait_for` | Pauses execution until a selector is visible/hidden. |
| `browser_evaluate` | Runs custom JavaScript in the page context. Use for complex data extraction. |
| `browser_press_key` | Simulates keyboard presses (Enter, Tab, Escape). |

## 3. Standard Workflow (Slow Path Discovery)
When performing a manual web task, adhere to this sequence:
1.  **Navigate:** `browser_navigate(url)`
2.  **Inspect:** `browser_snapshot()` - Analyze the output to find your target.
3.  **Act:** Use `browser_click`, `browser_fill_form`, etc., based on the snapshot.
4.  **Wait:** If the page changes, use `browser_wait_for` or `browser_snapshot` again.
5.  **Verify:** `browser_take_screenshot()` to confirm success for the "Live View".

## 4. Selector Best Practices
- **Prefer ARIA Roles:** `button[name="Submit"]`, `textbox[name="Username"]`.
- **Text Match:** `text="Login"` or `has-text("Sign Up")`.
- **Stable IDs:** `#login-btn`, `[data-testid="submit"]`.
- **Avoid Brittle Paths:** NEVER use `div > div > p:nth-child(3)`.

## 5. Network & Security
- **Localhost Resolution:** Because the Playwright MCP Server runs natively on the Host OS, you can safely use `http://localhost:[EXPOSED_PORT]` when hitting internal services. There is no need to worry about Docker network resolution or using `host.docker.internal`.
- **CRITICAL - Exposed Port Requirement:** When navigating to local services running in Docker (like the frontend), you MUST use the Host OS **exposed port** (e.g., `3001`) instead of the Docker internal port (e.g., `5173`). 
- **HTTPS Errors:** The browser is configured to ignore HTTPS errors by default to handle local dev environments.

## 6. Live View Synchronization ("The Eye")
All browser actions are logged and captured for the **Browser Dashboard**. 
- Console logs are automatically aggregated.
- Network requests are monitored.
- Screenshots are saved with unique IDs to provide a frame-by-frame history of the agent's actions.


### 6.1 State Synchronization (The "Navigation" Bug Lesson)
When bridging stateless API endpoints to a stateful UI monitoring system (like the Live View), **every** action that mutates the browser's visual state must trigger a state-sync event (e.g., an auto-captured screenshot).
- **The Mistake:** Previously, state-modifying actions like `browser_click` and `browser_type` correctly triggered auto-screenshots, but `browser_navigate` was mistakenly omitted because it was viewed as an "initialization" or "setup" step rather than a "mutation" step. This resulted in the UI retaining stale images after manual navigations.
- **The Rule:** Any interaction tool that fundamentally alters the DOM, URL, or rendered view—including `browser_navigate` and `browser_navigate_back`—MUST be strictly whitelisted to auto-trigger visual snapshots in the backend server routers. Never assume a navigation action is exempt from visual state synchronization.

## 7. Displaying Snapshots in Chat
- **Storage Path:** Screenshots taken via `browser_take_screenshot` are saved to the backend's `/api/tmp/` directory.
- **Rendering Protocol:** To render a snapshot in the chat, you MUST use the markdown syntax: `![filename](/api/tmp/filename)`.
- **Ephemeral Nature:** Images are stored in a temporary directory. They are NOT persistent in the database. If the `tmp/` folder is cleared, the image link in the chat history will break (404).
- **Tool Interception:** The backend automatically replaces the raw tool output with a JSON payload containing the `local_url` and a "Rendering Hint" message.
