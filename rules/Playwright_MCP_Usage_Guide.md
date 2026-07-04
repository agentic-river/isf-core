# 🎭 Playwright MCP Usage Guide

<!-- TRIGGER_KEYWORDS: go to, navigate, url, http, https, website, web portal, dashboard, host.docker.internal, localhost, click, interact, UI -->

## Objective
This document defines strict protocols for AI agents when interacting with the Playwright MCP browser-automation server (`playwright-mcp` container on port 8899). Following these rules prevents debugging loops caused by DOM hacking, React synthetic event bypass attempts, and blind selector guessing.

## 1. Core Principles & The Golden Rule

- **The Golden Rule: Cheapest Tool First.** Always use the least expensive tool that answers your question:
  1. 🥇 **`browser_network_requests()`** — "What data did the backend return?" (diagnose blank pages / wrong data in 1 call)
  2. 🥈 **`browser_keyword_search("text")`** — "Is this specific element on the page?" (searches ALL 10 attribute types + Shadow DOM, returns ~5 lines)
  3. 🥉 **`browser_snapshot()`** — "What's the full page structure?" (ARIA tree, thousands of lines — use when you need broad context)
  4. **`browser_take_screenshot()`** — "Does it look good?" (visual verification, heaviest payload)
- **Why this order matters:** A `browser_snapshot()` returns the entire DOM tree (can be 500+ lines). If you only need to know whether the API returned `[]` or the heading "Token Usage History" exists, `browser_network_requests()` or `browser_keyword_search()` gives you the answer in 3–5 lines — **10x faster and fewer tokens.**
- **Auto-Healing:** The MCP server automatically handles missing browser binaries.

```
✅ browser_navigate(url) → browser_network_requests() → diagnose data first
✅ browser_navigate(url) → browser_keyword_search("Dashboard") → verify element exists
✅ browser_navigate(url) → browser_snapshot() → then browser_click("text=Dashboard")
❌ browser_navigate(url) → browser_click("#elem-43752-random-hash") — guessing
❌ browser_navigate(url) → browser_snapshot() → ... → browser_snapshot() → ... → browser_snapshot() — snapshot loop
```

## 2. Selector Best Practices
- **Prefer ARIA Roles:** `button[name="Submit"]`, `textbox[name="Username"]`.
- **Text Match:** `text="Login"` or `has-text("Sign Up")`.
- **Stable IDs:** `#login-btn`, `[data-testid="submit"]`.
- **Avoid Brittle Paths:** NEVER use `div > div > p:nth-child(3)`.

## 3. Standard Workflow (Efficiency-Optimized)

When performing a manual web task, adhere to this sequence — **cheapest tool first**:

1.  **Navigate:** `browser_navigate(url)`
2.  **Diagnose (Network):** `browser_network_requests()` — Check if the page's API calls returned data or errors. **Skip this step if you are on a static page with no API dependency.**
3.  **Pinpoint (Keyword Search):** `browser_keyword_search("expected text")` — Verify your target element exists on the page without reading the entire DOM. Returns ~5 lines instead of 500+.
4.  **Inspect (Snapshot):** `browser_snapshot()` — Full ARIA tree. Use only when you need broad context the keyword search didn't provide (e.g., identifying all buttons in a toolbar, understanding page layout).
5.  **Act:** Use `browser_click`, `browser_fill_form`, etc., based on the discovered selectors.
6.  **Wait:** If the page changes, use `browser_wait_for` or go back to step 2 (network → keyword search → snapshot).
7.  **Verify:** `browser_take_screenshot()` to confirm visual success.

```
✅ browser_navigate(url) → browser_network_requests() → browser_keyword_search("Dashboard") → browser_click("text=Dashboard")
✅ browser_navigate(url) → browser_snapshot() → browser_click("text=Dashboard")  (static pages)
❌ browser_navigate(url) → browser_snapshot() → browser_click("#random-hash")  (guessing)
```

## 4. Tool Decision Matrix

| UI Pattern | ✅ USE THIS | ❌ NEVER USE |
|------------|------------|--------------|
| **Blank page / no data rendered** | 🥇 **`browser_network_requests()` FIRST** — check if API calls returned `[]`, 4xx, or 5xx. Then `browser_console_messages(level="error")` for JS crashes. Only then `browser_snapshot()` for DOM diagnosis. | `browser_snapshot()` as first tool — wastes tokens reading an empty ARIA tree when the root cause is in the network layer |
| **Can't identify how to click an element** seen in snapshot | `browser_search_keyword("text")` — searches ALL 10 attribute types (textContent, title, aria-label, placeholder, alt, class, id, name, value, href) across light + shadow DOM. Returns ancestor chains + clickable `selectorHint`. This is the **Tier 1 default fallback**. | Searching one attribute at a time (`textContent` → fail → `title` → fail → `aria-label` → fail ...) |
| Icon-only button (SVG child, empty textContent) | `browser_search_keyword("text")` — catches `title` and `aria-label` attributes automatically. Then click via the returned `selectorHint` (e.g. `button[title='Refresh Data']`). | `:has-text("Refresh Data")` — fails because `textContent` is empty |
| Native `<select>` dropdown | `browser_select_option(selector, value)` | DOM hacking with `dispatchEvent` |
| **Multiple** native `<select>` comboboxes | Use `:has()` to uniquely identify: `browser_select_option("select:has(option[value=\"MTD\"])", "All Time")` | `browser_select_option` with no selector — it will pick the first match, which may be the wrong one. Also avoid `select:first-of-type` — it matches across parent scopes and Playwright strict-mode rejects multi-match. |
| React/Vue custom dropdown | `browser_click("text=Dropdown")` → `browser_click("text=Option")` | `browser_select_option` — it silently fails |
| `text=` selector times out | `browser_click("text=MTD Cost")` auto-falls-back to `:has-text('MTD Cost')` (partial/contained match, more forgiving with React whitespace) | Manually retrying the same `text=` selector |
| Form text input | `browser_fill_form(selector, value)` | `browser_type` for whole-field fill |
| Virtualized / infinite-scroll table | `browser_scroll(direction, amount, container_selector)` loop + `browser_snapshot()` — scroll uses `behavior:'auto'` (synchronous) so `scrollY` reports immediately | `browser_evaluate("document.querySelector('...').scrollTop = ...")` |
| "Refresh Data" / "Apply" button that times out on click | `browser_evaluate("return Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Refresh'))?.click()")` — a one-liner JS click that bypasses Playwright's actionability checks is acceptable here as a last resort | Repeatedly retrying `browser_click` on an unresponsive button and burning iterations |
| Off-screen element | `browser_scroll_into_view(selector)` then `browser_click(selector)` | Clicking blind and hoping |
| Reading page data | `browser_snapshot()` (ARIA tree) or `browser_evaluate("return document.title")` | `browser_evaluate("return document.body.innerText")` |
| Debugging JS errors | `browser_console_messages(level="error")` | `browser_console_messages()` with no filter |

## 5. React / SPA Anti-Patterns (NEVER DO THESE)

These patterns waste iterations and fail on custom event systems:

```
❌ browser_run_code("document.querySelector('select').value = 'ALL'")
❌ browser_run_code("document.querySelector('select').dispatchEvent(new Event('change'))")
❌ browser_evaluate("React.__SECRET_INTERNALS...")
❌ browser_evaluate("Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')...")
❌ browser_run_code("nativeSetter.call(selectElement, 'ALL')")
```

### ⚠️ CRITICAL: STOP AND READ THIS FIRST

**Before typing ANY JavaScript hack**, ask yourself: *"Did I just try `browser_select_option` or `browser_click` and it didn't work?"* If yes, the problem is likely your **selector**, not the tool. DO NOT jump to `browser_run_code`. Instead:

1. Call `browser_snapshot()` and look at the ARIA tree.
2. Is it a `<select>` with `<option>` children? → `browser_select_option` WILL work — you just need the right selector.
3. Is it a `<div>` with role="listbox"? → It's a custom dropdown. Use `browser_click` to open it, then `browser_click` on the option.

**The correct approach is always:**
```
✅ browser_snapshot()  →  see the dropdown ARIA structure
✅ browser_click("text=Last 10 Days")  →  physically open the dropdown
✅ browser_snapshot()  →  see the option list
✅ browser_click("text=All Time")  →  physically click the option
```

## 6. Virtualized Table Protocol

Modern dashboards use virtualized tables that only render visible rows. To find a specific row:

```
1. browser_navigate(target_url) → browser_snapshot()
2. browser_click("text=Filter Dropdown") → browser_click("text=All Time")  # maximize range
3. browser_click("text=Refresh Data")   # <-- CRITICAL: many UIs need explicit refresh
   ⚠️ IF the "Refresh Data" button times out on click:
       - First: try browser_snapshot() to check if data already refreshed (some UIs auto-refresh on dropdown change)
       - Second: use browser_evaluate("return Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Refresh'))?.click()")
         as a one-liner JS fallback (bypasses Playwright actionability checks)
   ⚠️ IF a "Refresh" button UNRELATED to the data table appears (e.g., a "Refresh All" navigation button):
      STOP. Do NOT click it. It likely navigates away from the current page.
      Instead, use a more specific selector: browser_click("button[aria-label='Refresh Data']")
4. browser_snapshot() → identify the scrollable container's CSS selector
5. LOOP:
     browser_scroll("down", 500, ".table-container-class")  # scroll the container
     browser_snapshot() → search text for target date/value
     if found → extract data
     if reached end of list → stop
```

### ⚠️ Refresh Button Pitfalls

| Symptom | Do NOT | DO |
|---------|--------|----|
| `browser_click("text=Refresh Data")` → timeout | Retry `browser_click` 3+ times | Fall back to `browser_evaluate("return Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Refresh'))?.click()")` |
| Multiple "Refresh" buttons on page | Click the first one blind | Use a specific selector: `browser_click("button[aria-label='Refresh Data']")` or `browser_click("button:has-text('Refresh Data')")` — note the colon before `has-text` |
| Clicking "Refresh" navigates away | Panic | Use `browser_navigate_back()` to return, then use a more specific selector |

## 7. Network & Security

- **host.docker.internal Resolution:** Because the Playwright MCP Server runs in a Docker container on a bridge network, you MUST use `http://host.docker.internal:[EXPOSED_PORT]` when hitting local or internal services on the host. Using `localhost` will fail, as it resolves to the Playwright container itself.
- **CRITICAL - Exposed Port Requirement:** When navigating to local services running in Docker (like the frontend), you MUST use the Host OS **exposed port** (e.g., `3001`) instead of the Docker internal port (e.g., `5173`).
- **HTTPS Errors:** The browser is configured to ignore HTTPS errors by default to handle local dev environments.

### 7.2 Network-First Debugging Protocol

**When a page looks wrong (blank, missing data, stale), diagnose the network BEFORE inspecting the DOM.**

```
PROTOCOL (in order):
1. browser_network_requests()
   → Look for the API call that should have returned data
   → Check: Did it fire? (200? 4xx? 5xx? Not present at all?)
   → Check: What did the response body contain? ([]? error message? correct data?)

2. browser_console_messages(level="error")
   → Any JS runtime errors? (React crash, undefined variable, etc.)

3. browser_keyword_search("expected text")
   → Is any part of the expected UI actually in the DOM?

4. browser_snapshot()
   → Full ARIA tree — only when steps 1–3 didn't resolve the issue.
```

**Example: June 9 Empty Page Bug**
```
❌ WRONG: browser_snapshot() → "page is blank" → guess 10 different React fixes
✅ RIGHT: browser_network_requests() → API returned [] → check URL → date_filter clipped by time_range → fix backend in 30 seconds
```

## 8. Connection Architecture

```
Browser (Docker Container:8899) ← SSE → Backend (mcp_manager.py) → PlaywrightMCPWrapper (state.py) → LLM Tools
```

- The MCP server runs in a **Docker Container** on a bridge network + port `8899:8899`.
- From inside other Docker containers, reach it at `http://host.docker.internal:8899/sse`.
- From the Host OS, reach it at `http://localhost:8899/sse`.

## 9. Live View Synchronization & Snapshot Display

### 9.1 State Synchronization (The "Navigation" Bug Lesson)
When bridging stateless API endpoints to a stateful UI monitoring system (like the Live View), **every** action that mutates the browser's visual state must trigger a state-sync event (e.g., an auto-captured screenshot).
- **The Rule:** Any interaction tool that fundamentally alters the DOM, URL, or rendered view—including `browser_navigate` and `browser_navigate_back`—MUST be strictly whitelisted to auto-trigger visual snapshots in the backend server routers. Never assume a navigation action is exempt from visual state synchronization.

### 9.2 Displaying Snapshots in Chat
- **In-Memory Streaming:** Screenshots taken via Playwright MUST NOT be saved to publicly writable temporary directories (like `/tmp/` or `/api/tmp/`). They must be captured directly into memory as byte streams (`await page.screenshot(full_page=True)`).
- **Vision Ingestion:** To render or process a snapshot, upload the in-memory bytes to the GenAI Proxy via its `/v1/upload` endpoint. The proxy returns a `file_uri` that the vision model natively ingests.
- **Ephemeral Nature:** The returned URI is managed by the proxy and should be passed to the chat response structure to display inline.

## 10. `browser_run_code` & `browser_evaluate` IIFE Convention

Both `browser_run_code` and `browser_evaluate` auto-detect `return` prefixes
and wrap them in an IIFE.  Use `return` freely in either tool:

```
✅ browser_run_code("return document.querySelectorAll('tr').length")
✅ browser_evaluate("return document.title")
✅ browser_evaluate("return Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Refresh'))?.click()")
❌ browser_run_code("document.title")  -- no return, result will be "undefined"
```

**Key difference:**
- `browser_run_code` — ALWAYS wraps in IIFE (safe for multi-line code blocks).
- `browser_evaluate` — wraps in IIFE ONLY when the expression starts with `return`.
  Plain expressions like `document.title` are passed through directly to `page.evaluate()`.

## 11. Circuit Breaker Awareness

### 11.1 Architecture

The playwright-mcp server (`ai_manager/playwright_mcp.py`) maintains an `observation_count` on the `PlaywrightManager` singleton. This counter is:

| Tool | Increments? | Resets to 0? | Blocked by breaker? |
|------|------------|-------------|---------------------|
| `browser_snapshot` | ✅ +1 | ❌ | ✅ (after N consecutive) |
| `browser_click`, `browser_type`, `browser_navigate`, etc. (interaction) | ❌ | ✅ reset to 0 | ❌ |
| `browser_tabs`, `browser_console_messages`, `browser_network_requests` | ❌ | ❌ | ❌ (removed 2026-06-27) |
| `browser_evaluate` | ❌ | ✅ reset to 0 | ❌ |

The circuit breaker trips when `observation_count >= MCP_SNAPSHOT_CIRCUIT_BREAKER` (env var, default: `5`). To disable: `MCP_SNAPSHOT_CIRCUIT_BREAKER=0`.

### 11.2 AI Agent Guidance

If you hit the circuit breaker error ("Circuit Breaker: Infinite snapshot loop detected"), you MUST call a mutating tool (`browser_click`, `browser_type`, `browser_navigate`, `browser_scroll`) before the next `browser_snapshot()`.

### 11.3 Live View Polling Path (Internal)

The Live View dashboard (`GET /state`) polls every ~5s. As of 2026-06-27 it uses `browser_evaluate` for URL/title (NOT `browser_snapshot`) to avoid incrementing the observation counter. The `browser_tabs`, `browser_console_messages`, and `browser_network_requests` tools are also exempt from the circuit breaker since they don't increment the counter and can never cause an infinite-loop scenario.

If the backend logs show `Status 500: Circuit Breaker: Infinite observation loop detected` from the `isf-dev` container, it means the AI is calling `browser_snapshot` in a tight loop without intervening interactions — add a click/type/scroll between snapshots.

## 12. Non-Destructive Console & Network Reads

Both `browser_console_messages` and `browser_network_requests` are **non-destructive by default**. They return a copy of the buffer without clearing it. To clear after reading:
```
browser_console_messages(clear=True)
browser_network_requests(clear=True)
```
Use `browser_console_messages(level="error")` to filter only errors.

## 13. Quick Reference: All Available MCP Tools

| Tool | Purpose | Key Args |
|------|---------|----------|
| `browser_navigate` | Go to a URL | `url` |
| `browser_network_requests` | 🥇 **Network diagnostics (cheapest tool)** — API call log + response bodies. Use FIRST for blank pages or wrong data. | `clear`, `include_responses` |
| `browser_keyword_search` | 🥈 **One-shot element search across ALL 10 attribute types + Shadow DOM.** Returns ancestor chains + clickable `selectorHint`. **Tier 1 fallback for any click target.** | `keyword`, `case_sensitive`, `max_results` |
| `browser_snapshot` | 🥉 **Full ARIA tree + DOM summary.** Use when keyword search doesn't provide enough context. | `delay_ms` |
| `browser_take_screenshot` | 📸 **Visual verification (heaviest).** Use only for final confirmation or visual layout bugs. | `full_page` |
| `browser_click` | Click element (React-safe) | `selector` |
| | `browser_type` | Type character-by-character | `selector`, `text` |
| | `browser_fill_form` | Fill entire field at once | `selector`, `value` |
| | `browser_select_option` | Native `<select>` only | `selector`, `value` |
| | `browser_wait_for` | Wait for element state | `selector`, `state`, `timeout_ms` |
| | `browser_press_key` | Keyboard key press | `key` |
| | `browser_evaluate` | Run JS, return value | `expression` |
| | `browser_run_code` | Run JS (IIFE-wrapped) | `code` |
| | `browser_take_screenshot` | Base64 screenshot | `full_page` |
| | `browser_scroll` | Scroll page/container | `direction`, `amount`, `selector` |
| | `browser_scroll_into_view` | Scroll element into viewport | `selector` |
| | `browser_console_messages` | Read console logs | `level`, `clear` |
| `browser_network_requests` | 🥇 Read network log + response bodies | `clear`, `include_responses` |
| `browser_tabs` | List open tabs | — |
| `browser_close` | Close browser + reset | — |
| `browser_navigate_back` | Go back in history | — |
| `browser_resize` | Change viewport size | `width`, `height` |
| `browser_hover` | Hover over element | `selector` |
| `browser_drag` | Drag-and-drop | `source`, `target` |
| `browser_handle_dialog` | Accept/dismiss alert | `action`, `prompt_text` |
| `browser_file_upload` | Upload files | `selector`, `files` |

## 14. Auto-Healing: Session & Container Log Correlation

When a Playwright task fails or snapshots are missing, you MUST correlate the **session directory** logs with the **playwright-mcp container logs** to diagnose the root cause BEFORE attempting any fix.

### 14.1 Where the Logs Live

| Data Source | Location | How to Access |
|-------------|----------|---------------|
| **Session metadata** | `.browser_sessions/session_<ts>_<hash>/metadata.json` | `cat` or `read_file_content` |
| **Session snapshots** | `.browser_sessions/session_<ts>_<hash>/snapshots/` | `ls` the directory |
| **Playwright-MCP container log** | Container stdout/stderr (container name: `playwright-mcp`) | `docker logs playwright-mcp --tail 200` |
| **Backend app logs** | Container stdout/stderr (container name: `isf-prod` or `isf-dev`) | `docker logs isf-prod --tail 200` or `docker logs isf-dev --tail 200` |

### 14.2 Timestamp Correlation

**CRITICAL:** The two log sources use DIFFERENT time zones:

| Source | Time Zone | Example |
|--------|-----------|---------|
| `metadata.json` `created_at` / `started_at` | **GMT+0800 (SGT/MYT)** | `"2026-03-15T23:51:07.123456"` |
| playwright-mcp container log | **UTC** | `"2026-03-15 15:51:07,123 - playwright_mcp - INFO"` |

To correlate: **UTC = SGT - 8 hours**. A session that started at `23:51:07 SGT` corresponds to `15:51:07 UTC` in the playwright-mcp log.

### 14.3 Step-by-Step Diagnostic Protocol

When a session has `has_snapshot: false` for every step or snapshot images are missing:

```
1. ls .browser_sessions/
   → Identify the session_id (e.g., session_1782489067_466db63f)

2. cat .browser_sessions/<session_id>/metadata.json | python3 -c "import sys,json; m=json.load(sys.stdin); [print(f'{s[\"timestamp\"]} | {s[\"tool\"]:30s} | has_snap={s.get(\"has_snapshot\",False)} | result_preview={str(s.get(\"result\",\"\"))[:80]}') for s in m['steps']]"
   → Get the timeline of all steps and their snapshot status.

3. docker logs playwright-mcp --tail 300 2>&1 | grep -E "(browser_take_screenshot|browser_snapshot|browser_click|browser_navigate|ERROR|WARN)"
   → Find matching tool invocations. Note that mcp_manager.py sends auto-capture calls as browser_take_screenshot.

4. Cross-reference timestamps (subtract 8h from SGT to get UTC):
   - Does the playwright-mcp log show browser_take_screenshot calls at the same timestamps as steps?
   - Are there ERROR/WARN entries for those calls?

5. ls .browser_sessions/<session_id>/snapshots/
   → Count saved snapshot PNG files. Expected: 1 per interaction tool call.
```

### 14.4 Common Failure Patterns & Their Fixes

#### Pattern A: Zero Snapshots, Only Observation Tools Logged

**Symptoms:**
- `metadata.json` shows only `browser_snapshot`, `browser_tabs`, `browser_console_messages`, `browser_network_requests` steps
- All have `has_snapshot: false`
- Steps appear in repeating groups of 4 every ~5 seconds

**Root Cause:** Live View polling (`GET /state` in `backend/browser/server.py`) was flooding the session logger because every observation call was being recorded as a step with no snapshot.

**Fix (applied in `mcp_manager.py` / `server.py` / `state.py`):** Live View polling now passes `skip_log=True` to all four observation calls (`browser_snapshot`, `browser_tabs`, `browser_console_messages`, `browser_network_requests`). These calls are still executed and returned to the dashboard, but they are **not** recorded in the session logger. This eliminates ~80% of session log noise.

Additionally, `browser_snapshot` has been **removed** from the auto-capture exclusion list — AI-initiated `browser_snapshot()` calls now also capture a visual screenshot alongside the ARIA tree.

```
✅ Check: Are there interaction tool steps (click/navigate/type) with has_snapshot: false?
   If YES → Pattern B or C.
   If NO  → The session only had passive observation (Live View). No fix needed.
   If the session has NO Live View noise at all → skip_log=True is working correctly.
```

#### Pattern B: Interaction Tools Present But All `has_snapshot: false`

**Symptoms:**
- `metadata.json` has `browser_click` / `browser_navigate` / `browser_type` steps
- All have `has_snapshot: false`
- `snapshots/` directory is empty
- playwright-mcp log shows NO `browser_take_screenshot` calls at corresponding times

**Root Causes (check in order):**

1. **Fire-and-forget race condition:** `_capture_and_log_background()` is launched via `asyncio.create_task()` in `mcp_manager.py`. If the AI session terminates before the background task completes its HTTP round-trip to the playwright-mcp server, the snapshot is silently lost.

2. **Silent non-200 from playwright-mcp:** The auto-capture POST to `http://host.docker.internal:8899/rest/browser` returns a non-200 status. The code catches this (no exception is raised) but logs nothing — `_auto_capture_playwright_rest_snapshot()` silently returns `None`.

**Diagnostic command:**
```bash
# Check if any auto-capture calls reached the playwright-mcp container
docker logs playwright-mcp --tail 500 2>&1 | grep "browser_take_screenshot"

# If zero matches → the REST calls never reached the container (network issue, or background task never ran)
# If matches exist but no snapshots saved → the responses were non-200, check backend logs
docker logs isf-prod --tail 500 2>&1 | grep -i "capture\|screenshot\|snapshot"
# OR (if running on the dev container):
docker logs isf-dev --tail 500 2>&1 | grep -i "capture\|screenshot\|snapshot"
```

**Fixes applied (2025):**
- ✅ **Non-200 warning:** `_auto_capture_playwright_rest_snapshot()` now logs a warning when the REST call returns a non-200 status (including the response body prefix).
- ✅ **Error-path auto-capture:** Both `HTTPStatusError` and generic `Exception` paths in `execute_playwright_tool_via_rest()` now also fire `_capture_and_log_background()` (in addition to the direct `_log_playwright_step` call), so error states have a chance to capture a screenshot.
- ✅ **`browser_snapshot` auto-capture:** `browser_snapshot` is no longer excluded from auto-capture; AI snapshot calls now get an accompanying visual screenshot.
- ⚠️ **Background task still fire-and-forget:** The background task is still `asyncio.create_task()`; short-lived sessions may still miss snapshots. A future fix could await the capture synchronously for critical interaction tools.

#### Pattern C: Snapshots Exist But Don't Match Expected State

**Symptoms:**
- Snapshots are saved but show wrong/broken page
- `browser_take_screenshot` calls exist but the screenshot shows an error page or partial load

**Root Cause:** The auto-capture fires immediately after the tool returns success, but the page hasn't finished rendering (SPA transitions, lazy-loading, etc.).

**Fix:** The AI agent should add explicit waits after interaction tools:
```
✅ browser_click("text=All Time")
✅ browser_wait_for(3000)  // wait for SPA transition
✅ browser_snapshot()       // verify the new state
```

#### Pattern D: Playwright-MCP Container Unhealthy

**Symptoms:**
- All `browser_*` tool calls return errors
- `docker logs playwright-mcp` shows crash loops or `ERR_EMPTY_RESPONSE`

**Diagnostic:**
```bash
docker ps --filter name=playwright-mcp --format "{{.Status}}"
docker logs playwright-mcp --tail 50 2>&1 | grep -i "error\|crash\|fatal\|traceback"
```

**Fix:** Restart the container:
```bash
docker compose restart playwright-mcp
# Wait 5 seconds for health check
sleep 5
docker ps --filter name=playwright-mcp
```

#### Pattern E: Circuit Breaker Tripping on Live View Polling

**Symptoms:**
- `isf-dev` (or `isf-prod`) container log shows repeated `Status 500: Circuit Breaker: Infinite observation loop detected`
- The errors appear in groups at ~5s intervals
- Each error group has 4 calls: `browser_snapshot`, `browser_tabs`, `browser_console_messages`, `browser_network_requests`

**Root Cause:** Live View polling (`GET /state`) calls `browser_snapshot` every ~5s, which increments the `observation_count` in playwright-mcp. After 5 consecutive polls (25s) without any interaction tool, the counter hits 5 and the circuit breaker trips. This cascaded to `browser_tabs`, `browser_console_messages`, and `browser_network_requests` because those tools also checked the counter (before the 2026-06-27 fix).

**Fix (applied 2026-06-27):**
1. Removed the circuit breaker check from `browser_tabs`, `browser_console_messages`, `browser_network_requests` in `ai_manager/playwright_mcp.py` — these don't increment the counter and can never cause an infinite loop.
2. Replaced `browser_snapshot()` with `browser_evaluate()` in the Live View polling code (`backend/browser/server.py`). `browser_evaluate` resets `observation_count` to 0, so the breaker never trips from passive polling.

**Diagnostic command:**
```bash
# Check if Live View is using the old browser_snapshot path:
grep -n "browser_snapshot\|browser_evaluate" backend/browser/server.py

# The fix is in place if you see:
#   url_raw = await bt.browser_evaluate("return document.location.href", skip_log=True)
#   title_raw = await bt.browser_evaluate("return document.title", skip_log=True)
```

### 14.5 Session Directory Quick Reference

```
.browser_sessions/
└── session_<unix_ts>_<8char_hash>/
    ├── metadata.json          # Full step log with timestamps, tool names, results
    └── snapshots/             # Base64-decoded PNG files from auto-capture
        └── step_<index>.png   # One per interaction tool (when working correctly)
```

**`metadata.json` schema per step:**
```json
{
  "step_index": 0,
  "timestamp": "2026-03-15T23:51:07.123456",
  "tool": "browser_navigate",
  "args": {"url": "http://..."},
  "result": "Success: navigated to ...",
  "has_snapshot": false,
  "snapshot_path": null,
  "duration_ms": 1250
}
```

### 14.6 Self-Healing Checklist

Before reporting a Playwright failure to the user, the AI agent MUST complete this checklist:

- [ ] Read the session `metadata.json` — count `has_snapshot: true` vs `false` steps
- [ ] Check if interaction tools (click/navigate/type) have snapshots
- [ ] Run `docker logs playwright-mcp --tail 300` — check for ERROR/WARN entries
- [ ] Correlate timestamps (SGT = UTC + 8h) between session metadata and container logs
- [ ] Check `docker ps --filter name=playwright-mcp` — is the container healthy?
- [ ] Identify which Pattern (A/B/C/D) matches the symptoms
- [ ] Apply the documented fix or report with diagnostic data

## 15. Auto-Healing Portal Navigation Protocol

### 15.1 The Escalation Ladder (MANDATORY ORDER)

When navigating a **new or unknown portal**, the AI agent MUST follow this tiered escalation ladder **in strict order**. NEVER skip tiers — each tier exists to solve a specific class of failure without introducing unnecessary risk.

```
Tier 0 (Always)      →  Snapshot + Standard Playwright
Tier 1 (If timeout)  →  Selector Refinement (no JS yet)
Tier 2 (If still)    →  Shadow-DOM-aware DOM evaluation  
Tier 3 (Last resort) →  Forced JS interaction (bypasses all checks)
```

---

### 15.2 Tier 0: Snapshot-Driven Discovery (ALWAYS FIRST)

Standard approach. Works for 80%+ of portals. Already documented in §3.

```
✅ browser_navigate(url) → browser_snapshot() → identify element → browser_click / browser_select_option / browser_fill_form
```

**When to advance to Tier 1:** Element times out on click, matches wrong element, or `browser_select_option` picks the wrong `<select>`.

---

### 15.3 Tier 1: Selector Refinement (NO JavaScript Yet)

**Problem Pattern:** The element exists in the ARIA snapshot, but Playwright's selector matches the wrong element or times out due to a page quirk.

**FIRST FALLBACK — `browser_search_keyword` (covers 95% of cases in one call):**
Before trying individual refinements below, use `browser_search_keyword("your keyword")`. It searches ALL 10 attribute types (textContent, title, aria-label, placeholder, alt, class, id, name, value, href) across light + shadow DOM in a single call. It returns ancestor chains so you can build contextual selectors, and a `selectorHint` that's immediately clickable. **This replaces the old "search one attribute at a time" loop and catches icon-only buttons automatically.**

| Symptom | Refinement |
|---------|-----------|
| **Can't figure out HOW to click an element** seen in snapshot | 🌳 **`browser_search_keyword("keyword")`** — one call searches ALL attributes + Shadow DOM. Returns `selectorHint` + ancestor chain. Example: `browser_search_keyword("Refresh")` → finds `button[title='Refresh Data']` even with empty `textContent`. Then `browser_click("button[title='Refresh Data']")`. |
| Wrong `<select>` matched (multiple comboboxes) | `browser_select_option("select:has(option[value=\"ALL\"])", "All Time")` — use `:has()` to disambiguate |
| Click times out (element covered) | `browser_scroll_into_view("text=Refresh Data")` then `browser_click("text=Refresh Data")` |
| Click fires but page hasn't updated | `browser_wait_for(3000)` or `browser_wait_for("text=Expected Text", timeout=15000)` |
| Multiple identical text matches | `browser_click("button[aria-label='Refresh Data']")` or `browser_click("button:has-text('Refresh Data')")` |
| React/SPA custom dropdown (not native `<select>`) | `browser_click("text=Dropdown")` → `browser_snapshot()` → `browser_click("text=Option")` |

**When to advance to Tier 2:** Tier 1 refinements still fail, AND the element IS clearly visible in the ARIA snapshot but NOT reachable by any Playwright selector.

---

### 15.4 Tier 2: Shadow-DOM-Aware DOM Evaluation

#### 15.4.1 Diagnosing Shadow DOM

**The telltale sign:** `browser_snapshot()` shows the element clearly, but `document.querySelector()` returns `null` AND `browser_click()` times out or can't find it. This is the **"ARIA Sees It, DOM Doesn't"** pattern — the definitive signature of Shadow DOM.

```
✅ DIAGNOSTIC COMMAND (two-step):
   Step 1: browser_evaluate("return document.querySelector('YOUR-TARGET-SELECTOR') !== null")
           → If true → Element is in light DOM. NOT Shadow DOM.
              The issue is something else (disabled button, covered by overlay, etc.)
   Step 2: browser_evaluate("return !!document.querySelector('*')?.shadowRoot")
           → If true → Web components with Shadow DOM exist on the page (e.g., charts,
              icon libraries, micro-frontends). The target MAY be in a shadow root.
              Proceed to querySelectorDeep (§15.4.2) if target not found in light DOM.
           → If false → No shadow roots anywhere. Element genuinely not in DOM yet.
              Return to Tier 1, add browser_wait_for.

   ⚠️ FALSE POSITIVE WARNING: Even if Step 2 returns true, it only confirms that
   SOME element on the page uses Shadow DOM (very common with chart widgets, icon
   libraries, micro-frontends). It does NOT prove your target is in a shadow root.
   The definitive test is Step 1: can standard querySelector find your target?
```

#### 15.4.2 The `querySelectorDeep` Utility (MANDATORY)

When Shadow DOM is confirmed, use this recursive search function via `browser_evaluate`. It traverses **all** shadow roots to find elements that `document.querySelector` alone cannot reach:

```javascript
// Shadow-DOM-aware recursive querySelector
// browser_evaluate("return (function qsDeep(sel,root) { root=root||document; const all=[...root.querySelectorAll('*')]; for(const el of all) { if(el.matches(sel)) return el; if(el.shadowRoot) { const found=qsDeep(sel,el.shadowRoot); if(found) return found; } } return null; })('button')")
```

**Usage patterns:**
```
// Search for a button by text content across all shadow roots
browser_evaluate("return (function qsDeep(sel,root){root=root||document;const all=[...root.querySelectorAll('*')];for(const el of all){if(el.matches(sel))return el;if(el.shadowRoot){const found=qsDeep(sel,el.shadowRoot);if(found)return found;}return null;})('button')?.textContent")

// Click it (bypasses Playwright actionability)
browser_evaluate("return (function qsDeep(sel,root){root=root||document;const all=[...root.querySelectorAll('*')];for(const el of all){if(el.matches(sel))return el;if(el.shadowRoot){const found=qsDeep(sel,el.shadowRoot);if(found)return found;}return null;})('button').click()")
```

#### 15.4.3 XPath as a Text-Match Alternative

For elements with **fragmented text nodes** (e.g., `<button><span>Refresh</span> <span>Data</span></button>`), XPath's `contains(text(), ...)` can match where standard `textContent` iteration fails:

```
// Works: XPath sees the concatenated text content of <button> and all descendants
browser_evaluate("return document.evaluate(\"//button[contains(text(), 'Refresh')]\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click()")

// DOES NOT WORK for Shadow DOM — XPath is shadow-blind, same as querySelector
```

**⚠️ CRITICAL LIMITATION:** XPath CANNOT cross shadow boundaries. If the element is inside a shadow root, XPath will return `null` even when the ARIA snapshot shows it clearly. Use `querySelectorDeep` instead.

#### 15.4.4 Tier 2 Decision Flowchart

```
browser_snapshot() shows element?
  ├─ YES → browser_evaluate a SECOND snapshot to confirm page state hasn't changed
  │         (React may have re-rendered between your snapshot and your action).
  │     → browser_evaluate("return document.querySelector('YOUR-SELECTOR') !== null")
  │         ├─ Returns true → Element IS in light DOM. NOT Shadow DOM.
  │         │   The problem is something else: button is disabled, covered by overlay,
  │         │   or React state is stale from a dropdown change that didn't propagate.
  │         │   → Check: is the button disabled? browser_evaluate("return document.querySelector('button').disabled")
  │         │   → If disabled → the dropdown change didn't trigger React re-render.
  │         │      Use browser_select_option again (fixed: dispatches input + change),
  │         │      or for custom React dropdowns use browser_click sequence (§15.3).
  │         └─ Returns false → Element not in light DOM.
  │              → DIAGNOSE: browser_evaluate("return !!document.querySelector('*')?.shadowRoot")
  │                   ├─ true → Shadow DOM may exist → Use querySelectorDeep (§15.4.2)
  │                   │   ⚠️ FALSE POSITIVE RISK: Charts/icon libs use shadow DOM too.
  │                   │   This confirms shadow roots exist, NOT that your target is in one.
  │                   └─ false → Element genuinely not in DOM yet (loading/SPA).
  │                       Return to Tier 1, add browser_wait_for.
  └─ NO → Element genuinely not on page. Check for popups, redirects, or wrong page state.
```

---

### 15.5 Tier 3: Forced Interaction (ABSOLUTE LAST RESORT)

**⚠️ ONLY use when Tiers 0–2 have all been exhausted and documented.**

When an element exists in the DOM (confirmed via Tier 2) but cannot be interacted with due to Playwright's actionability checks (covered by overlay, `pointer-events: none`, zero dimensions, or animation in progress):

```
// Force-click — bypasses ALL Playwright actionability checks
browser_evaluate("return document.querySelector('button').click()")

// Force-value-set for <select> on React — dispatches both change + input events
browser_evaluate(`
  const sel = document.querySelector('select');
  const nativeSetter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
  nativeSetter.call(sel, 'ALL');
  sel.dispatchEvent(new Event('input', {bubbles: true}));
  sel.dispatchEvent(new Event('change', {bubbles: true}));
  return 'done';
`)
```

**⚠️ WARNING:** This tier is specifically for **React/SPA custom components** where standard `browser_select_option` and `browser_click` fail after Tiers 0–1. For standard native `<select>` elements, do NOT use this — `browser_select_option` with the correct selector will work.

---

### 15.6 Portal Navigation Auto-Healing Checklist (MANDATORY BEFORE GIVING UP)

Before reporting a navigation failure to the user, the AI agent MUST complete this checklist:

- [ ] **Tier 0:** Called `browser_snapshot()` and attempted standard Playwright interaction — documented what failed
- [ ] **Tier 1:** Tried at least 2 selector refinements (`:has()`, `[aria-label]`, `scroll_into_view`, `wait_for`)
- [ ] **Tier 1.5 — Disabled Button Check:** If a button (e.g., "Refresh Data") times out on click:
  - [ ] Called `browser_evaluate("return document.querySelector('BUTTON-SELECTOR')?.disabled")` to check if it's disabled
  - [ ] If disabled → the dropdown/input change that should enable it didn't propagate to React state
  - [ ] Re-do the dropdown change: `browser_select_option` (now dispatches `input` + `change`) or `browser_click` sequence for custom React dropdowns
  - [ ] After re-do: `browser_snapshot()` to verify the button is now enabled
- [ ] **Tier 2:** Ran the two-step Shadow DOM diagnostic (§15.4.1):
  - [ ] Step 1: `document.querySelector('TARGET-SELECTOR') !== null` → confirms light DOM presence
  - [ ] Step 2: `!!document.querySelector('*')?.shadowRoot` → general shadow root existence
  - [ ] If target NOT in light DOM AND shadow roots exist → attempted `querySelectorDeep`
  - [ ] If target NOT in light DOM AND no shadow roots → returned to Tier 1 with `browser_wait_for`
- [ ] **Tier 3:** If element found in DOM but unclickable → attempted JS `.click()` bypass
- [ ] Captured error-state screenshot via `browser_take_screenshot()` for diagnostic artifact
- [ ] Ran `browser_console_messages(level="error")` to check for JS runtime errors blocking the page
- [ ] Clearly stated which tier failed and why — provide evidence to user

---

### 15.7 Critical Bug Fix: `:has-text()` in `document.querySelector()`

**⛔ FORBIDDEN PATTERN:**
```js
// THIS WILL THROW SyntaxError IN EVERY BROWSER:
document.querySelector('button:has-text("Refresh")')
```

`:has-text()` is a **Playwright-specific pseudo-class**. It only exists in Playwright's selector engine (`page.locator()`, `browser_click()`). The browser's native `document.querySelector()` does NOT support it — this will always throw `DOMException: SyntaxError`.

**✅ CORRECT ALTERNATIVES:**

| Goal | Playwright Selector (use with `browser_click`) | JS DOM (use with `browser_evaluate`) |
|------|-----------------------------------------------|--------------------------------------|
| Find button containing text "Refresh" | `button:has-text("Refresh")` | `Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Refresh'))` |
| Find button with exact text | `button:text("Refresh Data")` | XPath: `//button[normalize-space()='Refresh Data']` |
| Find button with partial text (shadow-DOM-safe) | N/A | `querySelectorDeep` (see §15.4.2) |
