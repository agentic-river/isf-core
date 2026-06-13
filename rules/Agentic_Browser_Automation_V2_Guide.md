# 🤖 Agentic Browser Automation V2 & Routing Protocol

## Objective
This document outlines the architecture, routing rules, and script generation guidelines for the Agentic Browser Automation V2 lifecycle. It strictly defines how AI agents should route web automation tasks to avoid intent mismatches (e.g., confusing web portal interactions with SQL database queries) and how to transition from "Slow Path" discovery to "Fast Path" compiled execution.

## 1. Intent Routing & Tool Boundaries (MANDATORY)
- **Never Route Web Tasks to SQL:** When dealing with user requests mentioning "portal", "login", "external site", or interacting with a third-party application, agents MUST route to browser automation tools.
- **RESTRICT `query_federated_database` USAGE:** Under no circumstances should the `query_federated_database` tool be invoked to fetch data from web portals, HR systems, or third-party websites (e.g., leave balances, approvals). If a user requests an action on a "portal", strictly use the browser automation tools or the compiled portal tools.
- **Tool Constraint Specifications:** Internal database tools (e.g., `query_federated_database`) must maintain explicit constraints in their tool descriptions forbidding them from handling web automation or external application intents.

### 🟢 Good Example
*   **Good Tool Description:** "Fetches internal system metrics. DO NOT use this tool for tasks involving external websites, web portals, leave balances on third-party sites, or browser automation."

### 🔴 Bad Example
*   **Bad Tool Description:** "Fetches balances and user data." *(This is too broad and will cause the orchestrator to hallucinate an SQL table for things like "leave balances".)*

## 2. The Automation Lifecycle (Slow Path -> Fast Path)
Agents must follow this strict sequence for web tasks:
1. **Phase 1 - Credential Verification:** Before starting a web automation task requiring authentication, verify credentials exist in the `browser_credentials` table.
2. **Phase 2 - Discovery & Compilation (How to create the Fast Path script):** If no compiled script exists in `browser-agents/`:
   - **Step A (Discovery Protocol):** Use the **Native BrowserTools** (`browser_navigate`, `browser_snapshot`, `browser_fill_form`, `browser_click`) to manually achieve the user's goal once, subject to strict optimization rules:
     - **No Selector Guessing:** Always use `browser_snapshot()` before interaction. Construct selectors solely from the snapshot's output.
     - **Smart Waiting:** Pair every state-mutating action with `browser_wait_for`. Do NOT loop snapshots. **All waiting mechanisms MUST be capped at a maximum of 15 seconds (`timeout=15000`).**
     - **No JS Discovery:** Do not use `browser_evaluate` to find elements; only use it for final data extraction.
     - **Direct Navigation:** Prioritize direct URL navigation over clicking through UI menus when the destination URL is known.
   - **Step B:** Once successful, synthesize your steps into a robust, reusable async Playwright Python script.
   - **Step C:** Save this new file into the `browser-agents/` directory (e.g., `browser-agents/manage_leave_portal.py`). The script MUST include:
     - A Pydantic schema for inputs (`SubmitLeaveSchema`).
     - A `TASK_METADATA` dictionary defining the tool `name`, `description`, `domain` (for credential lookup), and `schema`.
     - An `async def run_task(inputs, credentials)` entry point.
     - Defensive validation to ensure `credentials` contains the required keys before interaction.
     - Logic to handle `.json` state caching in the persistent volume `/app/backend/data/browser_sessions` (NOT a relative `sessions/` path) to bypass future logins and avoid Docker permission errors.
3. **Phase 3 - Fast Path Execution:** Scripts compiled into `browser-agents/` must be dynamically registered as first-class tools (e.g., `manage_employee_leave_portal`). Future identical requests must be routed directly to this compiled tool, completely skipping the Discovery mode.

## 3. Fast Path Script Generation & Refinement Rules
When the AI generates or refines Python scripts for `browser-agents/`, it must adhere to these resilience standards:
- **Avoid Brittle Selectors:** NEVER use exact HTML table indices or rigid DOM paths. Use text-based filtering (e.g., `locator('tr').filter(has_text='Annual')`).
- **Robust Navigation (ASP.NET/SPA):** Handle postbacks and dynamic loads safely. Prefer `page.wait_for_load_state('networkidle')` or explicit element waits over deprecated `wait_for_navigation`.
- **Credential Mapping:** Ensure custom parameters (e.g., `COMPANY_NAME`) are correctly extracted from the `input_schema` JSONB field of the `browser_credentials` table rather than hardcoded.
- **State Caching:** Leverage saved authentication states using the absolute persistent volume path (e.g., `/app/backend/data/browser_sessions/*.json`) to skip login screens and accelerate script execution. NEVER use relative paths like `sessions/` as they will cause permission errors in the Docker container.
- **Security & Naming:** All `agent_id` identifiers MUST be validated against a strict regular expression `r"^[a-zA-Z0-9_]+$"` to ensure they only contain alphanumeric characters and underscores, preventing path traversal and ensuring consistent filenames.
- **DNS Resiliency inside Docker (MANDATORY):** Headless Chromium inside Docker containers often fails to resolve private or VPN corporate domains due to its built-in asynchronous DNS engine. You MUST launch Chromium with the `--disable-features=AsyncDns` flag to force it to use the container's standard OS-level DNS resolver (e.g., `await p.chromium.launch(headless=True, args=["--disable-features=AsyncDns"])`).

## 4. Phase 4 - Automated Verification (MANDATORY TEST HARNESS)
Agents MUST NOT ask the user to manually test newly generated or modified "Fast Path" scripts. 
Whenever a script in `browser-agents/` is created or modified, the agent MUST run the local test harness:
`python backend/core/testing_tools/test_browser_agent.py`
If the test harness fails or throws an error (such as a database schema mapping mismatch or an ASP.NET postback crash), the AI MUST debug and fix the script until the test harness passes perfectly BEFORE informing the user that the task is complete.



## 5. Phase 5 - Workspace Cleanup (MANDATORY)
Agents MUST clean up any temporary scripts, debug logs, intermediate state files, or leftover artifacts (excluding expected persistent session caches like `/app/backend/data/browser_sessions/*.json`) created during the discovery, compilation, or testing phases of a task. Maintaining a clean workspace upon task completion is critical to avoiding repository clutter and potential conflicts in future runs.

## 6. Fast Path Design Template (MANDATORY)
All "Fast Path" scripts in `browser-agents/` MUST follow this structure to ensure compatibility with the vault and backend routing:

```python
import os
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AgentTaskSchema(BaseModel):
    # Define inputs here
    action: str = Field(..., description="Action to perform")

TASK_METADATA = {
    "name": "my_portal_agent",
    "description": "Performs actions on the XYZ Portal",
    "domain": "example-portal.com", # CRITICAL: Used for vault lookup
    "schema": AgentTaskSchema.model_json_schema()
}

async def run_task(inputs: Dict[str, Any], credentials: Dict[str, Any]):
    # 1. Defensive Credential Validation (MANDATORY)
    username = credentials.get("username") or credentials.get("USERNAME", "")
    password = credentials.get("password_encrypted") or credentials.get("password") or credentials.get("PASSWORD", "")

    if not username or not password:
        return {
            "status": "error",
            "message": f"Missing credentials in vault for domain: {TASK_METADATA['domain']}"
        }

    # 2. Define Persistent Session Directory (MANDATORY)
    SESSION_DIR = '/app/backend/data/browser_sessions'
    os.makedirs(SESSION_DIR, exist_ok=True)
    session_path = os.path.join(SESSION_DIR, f"{TASK_METADATA['name']}.json")

    # 3. Browser launch with standard DNS routing (MANDATORY)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-features=AsyncDns"] # Bypasses internal Chromium DNS issues on VPNs
        )
        # Load or create storage state safely
        state_exists = os.path.exists(session_path) and os.path.getsize(session_path) > 0
        context = await browser.new_context(
            storage_state=session_path if state_exists else None,
            ignore_https_errors=True
        )
        page = await context.new_page()

        # 4. Browser logic with safe fills
        # await page.goto(f"https://{TASK_METADATA['domain']}")
        # await page.fill("#user", username)
        # ...
        
        await context.storage_state(path=session_path)
        await browser.close()
```

## 7. Defensive Execution Protocol
- **Zero-Null Fill:** NEVER call `page.fill()` or `page.type()` with a variable that hasn't been validated as a non-empty string.
- **Graceful Faults:** If credentials or required inputs are missing, return a JSON object with `status: "error"` and a descriptive message instead of letting the script throw a Python exception.
- **DNS Resiliency inside Docker (MANDATORY):** Headless Chromium inside Docker containers often fails to resolve private or VPN corporate domains due to its built-in asynchronous DNS engine. You MUST launch Chromium with the `--disable-features=AsyncDns` flag to force it to use the container's standard OS-level DNS resolver (e.g. `browser = await p.chromium.launch(headless=True, args=["--disable-features=AsyncDns"])`).

## 8. Visual Debugging & Offline Screenshot Protocol

### 8.1 Rationale
Layer 3 scripts (`browser-agents/`) run their own headless Chromium, completely independent of the Playwright MCP server. This means they can capture screenshots **even when MCP is offline**. By returning screenshot file URIs from error states, the AI agent can visually inspect failures and autonomously self-heal.

The Three-Layer Architecture:
- **Layer 1: Interactive Playwright MCP Server** — Node.js persistent browser, online-only, single point of failure.
- **Layer 2: Thin Wrappers & Delegators** — `PlaywrightMCPWrapper` + `browser/server.py` HTTP router, delegates to Layer 1, returns empty string when MCP offline.
- **Layer 3: Standalone Dynamic Browser Scripts** — `browser-agents/*.py` with own headless Chromium, always works, independently capable of screenshots + vision ingestion.

### 8.2 Mandatory Debug Screenshot Helper
All Layer 3 scripts MUST include the following helper function and invoke it whenever an error or unexpected state occurs:

```python
import os
import httpx

async def _capture_and_upload_screenshot(page, label: str = "debug") -> str:
    """
    Take a full-page screenshot, upload to the AI proxy, and return a file_uri
    for multimodal vision ingestion by the AI agent.
    
    Args:
        page: Playwright Page object
        label: Descriptive label for the screenshot filename
    
    Returns:
        A file_uri string (e.g., "gs://...") that the AI's vision model can ingest.
        Returns None if upload fails.
    """
    task_name = TASK_METADATA["name"]
    filename = f"{task_name}_{label}.png"
    path = f"/tmp/{filename}"
    
    await page.screenshot(path=path, full_page=True)
    
    proxy_url = f"{os.getenv('AI_PROXY_URL', 'http://localhost:8080')}/v1/upload"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(path, "rb") as f:
                resp = await client.post(
                    proxy_url,
                    files={"file": (filename, f, "image/png")}
                )
                resp.raise_for_status()
                upload_data = resp.json()
        return upload_data.get("file_uri")
    except Exception as e:
        print(f"[Screenshot] Upload failed: {e}")
        return None
```

### 8.3 Mandatory Error-State Screenshot Capture
Every `except` block and unexpected state handler in Layer 3 scripts MUST call `_capture_and_upload_screenshot` and include the `file_uri` + `mime_type` in the returned error dictionary:

```python
async def run_task(inputs, credentials) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-features=AsyncDns"])
        ...
        try:
            await page.wait_for_selector("tr", timeout=15000)
        except Exception as e:
            file_uri = await _capture_and_upload_screenshot(page, "error_state")
            return {
                "status": "error",
                "message": f"Selector timeout: {str(e)}",
                "file_uri": file_uri,
                "mime_type": "image/png"
            }
```

### 8.4 Optional Success-State Screenshot
For critical actions (approvals, submissions, data extraction), scripts SHOULD also capture a success screenshot to provide visual confirmation:

```python
# After successful data extraction or form submission
file_uri = await _capture_and_upload_screenshot(page, "success")
return {
    "status": "success",
    "message": "Successfully retrieved 42 applications.",
    "data": data,
    "file_uri": file_uri,
    "mime_type": "image/png"
}
```

### 8.5 Why This Works (End-to-End Flow)
1. `page.screenshot(path=..., full_page=True)` captures a local PNG — no MCP dependency.
2. Upload to proxy via `/v1/upload` generates a cloud URI.
3. Returning `file_uri` + `mime_type` triggers `_append_vision_data()` in `backend/core/proxy_client/tool_executor.py`.
4. The multimodal vision model receives the screenshot as a `Part.from_uri()` on the next conversation turn.
5. The AI can visually diagnose layout failures, missing selectors, loading spinners, or unexpected redirects — and autonomously fix the script.

### 8.6 Mandatory ARIA Snapshot for Text-Based Diagnosis
In addition to screenshots, ALL Layer 3 scripts MUST capture the **ARIA accessibility snapshot** of the page. This provides a compact (2–30 KB), semantic, YAML-like representation of the DOM that any text-only LLM can parse instantly — no vision model required.

```python
async def _capture_aria_snapshot(page) -> str:
    """
    Capture the ARIA accessibility tree of the current page.
    Returns a compact semantic YAML-like representation of all
    interactable elements, landmarks, and their states.

    This is 10-50x smaller than raw HTML and reveals hidden state
    (overlays, disabled buttons, loading spinners) that even a
    screenshot might miss.

    Args:
        page: Playwright Page object

    Returns:
        A YAML-like string of the accessibility tree.
        Returns empty string on failure.
    """
    try:
        aria_tree = await page.locator("body").aria_snapshot()
        return aria_tree or ""
    except Exception as e:
        print(f"[ARIA] Snapshot failed: {e}")
        return ""
```

### 8.7 The Three Approaches Compared
When diagnosing a navigation failure, use this tiered strategy:

| Tier | Tool | Size | Cost | Detects | When to Use |
|:---|:---|:---|:---|:---|:---|
| **1. ARIA Snapshot** | `page.locator("body").aria_snapshot()` | 2–30 KB | Text LLM (~$0.0001) | Overlays, disabled buttons, loading spinners, missing elements, redirect state | **Always — first line of diagnosis** |
| **2. Screenshot** | `page.screenshot(full_page=True)` | 20–200 KB | Vision model (~$0.01-0.03) | CSS/layout bugs, pixel alignment, visual regressions | When ARIA doesn't reveal the root cause |
| **3. Raw HTML** | `page.content()` | 100–500+ KB | Text LLM (high token cost) | Hidden `<script>` data, `data-*` attributes, CSS class chains | **Last resort only** |

**Why ARIA snapshots are so effective:**
- They show `button "Approve" [disabled]` — raw HTML can't convey disabled state.
- They show `dialog "Loading..."` — revealing overlay blockers that screenshots can miss if the spinner is transparent.
- They exclude `<script>`, `<style>`, and invisible wrapper `<div>`s — no token waste.

### 8.8 Mandatory Error-State Response Format
Every error return from a Layer 3 script MUST include BOTH `aria_snapshot` AND `file_uri`:

```python
except PlaywrightTimeoutError as e:
    aria = await _capture_aria_snapshot(page)
    file_uri = await _capture_and_upload_screenshot(page, "error_timeout")
    return {
        "status": "error",
        "message": f"Timeout: {str(e)}",
        "aria_snapshot": aria,        # Free text-based diagnosis
        "file_uri": file_uri,          # Visual confirmation
        "mime_type": "image/png"
    }
```

The AI agent will:
1. Read `aria_snapshot` first (cheap, text-based, instant diagnosis).
2. Use `file_uri` for multimodal visual confirmation only if needed.
3. This two-pronged approach means the agent can self-heal even if the vision model is offline or rate-limited.
