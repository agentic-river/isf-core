from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError, BrowserContext, Locator
import os
import json
import asyncio
import re
import httpx
import aiofiles

# Constants
IMAGE_PNG_MIME_TYPE = "image/png"
SIGNIN_URL = 'https://sg-eleave.mmh-global.com/eportalV2/public/signin.aspx'
APPLY_LEAVE_URL = 'https://sg-eleave.mmh-global.com/eportalV2/leave/organizer/applyleave.aspx'
PROCESS_LEAVE_URL = 'https://sg-eleave.mmh-global.com/eportalV2/leave/processor/processleave.aspx'

# 1. Strong Type Input Schema
class ManageLeaveSchema(BaseModel):
    action: Literal["get_pending_approvals", "approve_leaves", "get_leave_balance", "apply_leave", "get_leave_history", "get_leave_approver"] = Field(
        ..., description="The action to perform on the leave portal."
    )
    # Fields for 'apply_leave'
    leave_type: Optional[str] = Field(None, description="Type of leave (e.g., Annual, Sick). Required for 'apply_leave'.")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD). Required for 'apply_leave'.")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD). Required for 'apply_leave'.")
    reason: Optional[str] = Field(None, description="Reason for leave. Optional for 'apply_leave'.")
    # Fields for 'approve_leaves'
    leave_ids_to_approve: Optional[str] = Field(None, description="Comma-separated list of leave application IDs to approve. Required for 'approve_leaves'.")

# 2. Metadata for Orchestrator
TASK_METADATA = {
    "name": "eLeave_Portal",
    "description": "Performs actions on the employee leave portal: gets pending approvals, approves leaves, gets balance, applies for leave, retrieves history, and gets leave approver.",
    "domain": "sg-eleave.mmh-global.com",
    "schema": ManageLeaveSchema
}

async def _capture_aria_snapshot(page: Page) -> str:
    """
    Capture the ARIA accessibility tree of the current page.
    Returns a compact semantic YAML-like representation of all
    interactable elements, landmarks, and their states.

    This is 10-50x smaller than raw HTML and reveals hidden state
    (overlays, disabled buttons, loading spinners) that even a
    screenshot might miss.
    """
    try:
        aria_tree = await page.locator("body").aria_snapshot()
        return aria_tree or ""
    except Exception as e:
        print(f"[ARIA] Snapshot failed: {e}")
        return ""


async def _capture_and_upload_screenshot(page: Page, label: str = "debug") -> Optional[str]:
    """
    Take a full-page screenshot, upload to the AI proxy, and return a file_uri
    for multimodal vision ingestion by the AI agent.
    """
    task_name = TASK_METADATA["name"]
    filename = f"{task_name}_{label}.png"
    path = f"/tmp/{filename}"
    await page.screenshot(path=path, full_page=True)
    proxy_url = f"{os.getenv('AI_PROXY_URL', 'http://localhost:8080')}/v1/upload"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with aiofiles.open(path, "rb") as f:
                content = await f.read()
                resp = await client.post(
                    proxy_url,
                    files={"file": (filename, content, IMAGE_PNG_MIME_TYPE)}
                )
                resp.raise_for_status()
                upload_data = resp.json()
        return upload_data.get("file_uri")
    except Exception as e:
        print(f"[Screenshot] Upload failed: {e}")
        return None

def _parse_leave_ids(raw_ids: Optional[str]) -> List[str]:
    if not raw_ids:
        return []
    try:
        # Try parsing as JSON list first
        parsed = json.loads(raw_ids)
        if isinstance(parsed, list):
            return [str(i) for i in parsed]
        else:
            return [str(parsed)]
    except Exception:
        # Fallback to comma-separated or single ID
        return [i.strip() for i in raw_ids.split(",") if i.strip()]

async def _select_company(page: Page, company_name: str) -> None:
    try:
        # Find the value to select to avoid race conditions during PostBack
        dropdown = page.locator('#MainContent_ddlCompany')
        options = dropdown.locator('option')
        count = await options.count()

        target_val = None
        target_text = ""
        search_term = company_name.split('[')[0].strip().lower() if '[' in company_name else company_name.lower()

        for i in range(count):
            text = await options.nth(i).inner_text()
            if text:
                # Exact match check
                if text.strip() == company_name:
                    target_val = await options.nth(i).get_attribute('value')
                    target_text = text
                    break
                # Partial match check
                elif search_term in text.lower():
                    target_val = await options.nth(i).get_attribute('value')
                    target_text = text

        if target_val:
            print(f"[Auth] Attempting to select company: '{target_text}' (value: {target_val})")
            try:
                # ASP.NET __doPostBack causes a page reload. We must wait for it.
                async with page.expect_navigation(wait_until='networkidle', timeout=10000):
                    await dropdown.select_option(value=target_val)
                print("[Auth] PostBack navigation completed.")
            except PlaywrightTimeoutError:
                print("[Auth] Company selected, but no navigation detected. Waiting for network idle.")
                await page.wait_for_load_state('networkidle')
        else:
            print(f"[Auth] Warning: Could not find any option matching '{company_name}'")

    except Exception as e:
        print(f"[Auth] Warning: Could not select company dropdown: {e}")

async def _authenticate_portal(page: Page, credentials: Dict[str, Any], context: BrowserContext, session_path: str, session_dir: str) -> Dict[str, Any]:
    print("[Auth] Session expired or missing. Attempting login...")
    # Extract Extra Fields from Vault (Vault passes extra fields directly into credentials)
    # Handle varying dictionary schemas from state.py
    input_schema = credentials.get('input_schema', {}) or {}
    company_name = input_schema.get('COMPANY_NAME') or credentials.get('COMPANY_NAME', 'MUSIM MAS HOLDINGS PTE. LTD. [EPEMusimma]')

    # Handle both raw db fields and capitalized standard fields
    username = credentials.get('username') or credentials.get('USERNAME', '')
    password = credentials.get('password_encrypted') or credentials.get('password') or credentials.get('PASSWORD', '')

    if not username or not password:
        return {"success": False, "error": "Authentication failed. Missing username or password in vault."}

    await _select_company(page, company_name)

    # Ensure DOM is ready and inputs are visible *after* the PostBack
    await page.wait_for_selector('#MainContent_txtEmpID', state='visible')
    await page.fill('#MainContent_txtEmpID', username)
    await page.fill('#MainContent_txtPassword', password)

    async with page.expect_navigation(wait_until='networkidle'):
        await page.click('#MainContent_btnSignIn')

    if "signin" in page.url.lower() or "login" in page.url.lower():
        return {"success": False, "error": "Authentication failed. Check credentials."}

    os.makedirs(session_dir, exist_ok=True)
    await context.storage_state(path=session_path)
    print("[Auth] Session state saved successfully.")
    return {"success": True}

# 3. Execution Engine
async def _route_action(page: Page, inputs: ManageLeaveSchema) -> Dict[str, Any]:
    if inputs.action == "get_pending_approvals":
        return await _get_pending_approvals(page)
    if inputs.action == "approve_leaves":
        leave_ids = _parse_leave_ids(inputs.leave_ids_to_approve)
        return await _approve_leaves(page, leave_ids)
    if inputs.action == "get_leave_balance":
        return await _get_leave_balance(page)
    if inputs.action == "apply_leave":
        return await _apply_leave(page, inputs.leave_type, inputs.start_date, inputs.end_date, inputs.reason)
    if inputs.action == "get_leave_history":
        return await _get_leave_history(page)
    if inputs.action == "get_leave_approver":
        return await _get_leave_approver(page)
    
    return {"success": False, "error": f"Unsupported action: {inputs.action}"}


async def run_task(inputs: ManageLeaveSchema, credentials: Dict[str, Any]) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-features=AsyncDns"])
        SESSION_DIR = '/app/backend/data/browser_sessions'
        session_path = os.path.join(SESSION_DIR, 'sg-eleave.json')

        # Fast Path (Session State)
        context = await browser.new_context(
            storage_state=session_path if os.path.exists(session_path) else None,
            ignore_https_errors=True
        )
        page = await context.new_page()

        try:
            portal_url = credentials.get('DOMAIN', SIGNIN_URL)
            if not portal_url.startswith('http'):
                portal_url = f"https://{portal_url}/eportalV2/public/signin.aspx"

            await page.goto(portal_url, wait_until='domcontentloaded')
            await page.wait_for_load_state('networkidle')

            # Auth fallback if session is missing or expired
            if "signin" in page.url.lower() or "login" in page.url.lower():
                auth_res = await _authenticate_portal(page, credentials, context, session_path, SESSION_DIR)
                if not auth_res.get("success"):
                    return auth_res

            # Routing based on action
            result = await _route_action(page, inputs)
            if not result.get("success") and "error" in result and result["error"].startswith("Unsupported action:"):
                return result

            if result.get("success"):
                file_uri = await _capture_and_upload_screenshot(page, "success")
                result["aria_snapshot"] = await _capture_aria_snapshot(page)
                result["file_uri"] = file_uri
                result["mime_type"] = IMAGE_PNG_MIME_TYPE
            return result

        except PlaywrightTimeoutError as e:
            aria = await _capture_aria_snapshot(page)
            file_uri = await _capture_and_upload_screenshot(page, "error_timeout")
            return {"success": False, "error": f"Timeout Error: {str(e)}", "drift_detected": True, "aria_snapshot": aria, "file_uri": file_uri, "mime_type": IMAGE_PNG_MIME_TYPE}
        except Exception as e:
            aria = await _capture_aria_snapshot(page)
            file_uri = await _capture_and_upload_screenshot(page, "error_state")
            return {"success": False, "error": str(e), "aria_snapshot": aria, "file_uri": file_uri, "mime_type": IMAGE_PNG_MIME_TYPE}
        finally:
            await browser.close()

# Internal Helper Functions mapped to ASP.NET DOM
async def _get_pending_approvals(page: Page) -> Dict[str, Any]:
    await page.goto(PROCESS_LEAVE_URL, wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    approvals = []
    # Use a broader locator to find the grid safely
    table_locator = page.locator('table').filter(has_text=re.compile(r'Leave|Date|Employee', re.IGNORECASE)).first

    if await table_locator.count() > 0:
        rows = table_locator.locator('tr')
        count = await rows.count()
        # Skip header
        for i in range(1, count):
            cells = rows.nth(i).locator('td')
            # Require at least 10 columns based on the exact UI mapping:
            # 0: Checkbox, 1: S/N, 2: Trans ID, 3: Emp ID, 4: Name, 5: Type
            # 6: Submitted Date, 7: From, 8: To, 9: Duration
            if await cells.count() >= 10:
                approvals.append({
                    "trans_id": (await cells.nth(2).inner_text()).strip(),
                    "emp_id": (await cells.nth(3).inner_text()).strip(),
                    "name": (await cells.nth(4).inner_text()).strip(),
                    "type": (await cells.nth(5).inner_text()).strip(),
                    "submitted_date": (await cells.nth(6).inner_text()).strip(),
                    "from_date": (await cells.nth(7).inner_text()).strip(),
                    "to_date": (await cells.nth(8).inner_text()).strip(),
                    "duration": (await cells.nth(9).inner_text()).strip()
                })
    return {"success": True, "data": approvals}

async def _approve_leaves(page: Page, leave_ids: List[str]) -> Dict[str, Any]:
    await page.goto(PROCESS_LEAVE_URL, wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    approved_count = 0
    for leave_id in leave_ids:
        row = page.locator('tr').filter(has_text=leave_id).first
        if await row.count() > 0:
            chk = row.locator('input[type="checkbox"]').first
            if await chk.count() > 0 and not await chk.is_checked():
                await chk.check()
                approved_count += 1

    if approved_count > 0:
        submit_btn = page.locator('input[type="submit"], button').filter(has_text=re.compile(r'Approve', re.IGNORECASE)).first
        if await submit_btn.count() > 0:
            async with page.expect_navigation(wait_until='networkidle'):
                await submit_btn.click()

    return {"success": True, "approved_count": approved_count}

async def _parse_table(table_locator: Locator) -> Dict[str, str]:
    balances = {}
    if await table_locator.count() > 0:
        full_table = table_locator.first.locator('tr')
        count = await full_table.count()
        for i in range(1, count):
            cells = full_table.nth(i).locator('td')
            if await cells.count() >= 2:
                leave_type = await cells.nth(0).inner_text()
                balance_text = await cells.nth(1).inner_text()
                # Clean up balance text
                parts = balance_text.strip().split('\\n')
                val = parts[0].strip() if parts else balance_text.strip()
                if leave_type and val:
                    balances[leave_type] = val
    return balances

async def _get_leave_balance(page: Page) -> Dict[str, Any]:
    await page.goto(APPLY_LEAVE_URL, wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    tables = page.locator('table.JTable, table.table')
    balances = await _parse_table(tables)

    full_year_balances = {}
    try:
        tab = page.locator('text="View Full Year Entitlement"').first
        if await tab.count() > 0:
            await tab.click()
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(1) # wait for render

            tables2 = page.locator('table.JTable, table.table')
            full_year_balances = await _parse_table(tables2)
    except Exception:
        pass

    if not balances and not full_year_balances:
        return {"success": False, "error": "Could not parse entitlement balances."}

    return {"success": True, "data": {"ytd_balance": balances, "full_year_entitlement": full_year_balances}}

async def _apply_leave(page: Page, leave_type: Optional[str], start_date: Optional[str], end_date: Optional[str], reason: Optional[str]) -> Dict[str, Any]:
    await page.goto(APPLY_LEAVE_URL, wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    if leave_type:
        await page.locator('select').filter(has_text=re.compile(r'Annual|Sick|Maternity', re.IGNORECASE)).first.select_option(label=leave_type)

    if start_date:
        await page.fill('input[name*="From"]', start_date)
    if end_date:
        await page.fill('input[name*="To"]', end_date)

    if reason:
        await page.fill('textarea, input[name*="Remark"]', reason)

    btn = page.locator('input[type="submit"], button').filter(has_text=re.compile(r'Submit|Apply', re.IGNORECASE)).first
    if await btn.count() > 0:
        async with page.expect_navigation(wait_until='networkidle'):
            await btn.click()

    return {"success": True, "message": "Leave submitted successfully."}

async def _get_leave_history(page: Page) -> Dict[str, Any]:
    await page.goto('https://sg-eleave.mmh-global.com/eportalV2/home.aspx', wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    leave_status_btn = page.locator('a, span, div, li').filter(has_text=re.compile(r'^Leave Status$', re.IGNORECASE)).first
    await leave_status_btn.click()
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(1)

    history = []
    # Identify history table robustly
    tables = page.locator('table').filter(has_text=re.compile(r'Trans ID', re.IGNORECASE))
    if await tables.count() > 0:
        rows = tables.first.locator('tr')
        count = await rows.count()

        for i in range(1, count):
            cells = rows.nth(i).locator('td')
            cell_count = await cells.count()
            if cell_count >= 7:
                history.append({
                    "trans_id": (await cells.nth(0).inner_text()).strip(),
                    "from_date": (await cells.nth(1).inner_text()).strip(),
                    "to_date": (await cells.nth(2).inner_text()).strip(),
                    "leave_type": (await cells.nth(3).inner_text()).strip(),
                    "submitted_on": (await cells.nth(4).inner_text()).strip(),
                    "request_type": (await cells.nth(5).inner_text()).strip(),
                    "status": (await cells.nth(6).inner_text()).strip()
                })

    return {"success": True, "data": history}

async def _get_leave_approver(page: Page) -> Dict[str, Any]:
    await page.goto(APPLY_LEAVE_URL, wait_until='domcontentloaded')
    await page.wait_for_load_state('networkidle')

    approver_locator = page.locator('#MainContent_lblApprovingManager')
    if await approver_locator.count() > 0:
        approver_name = await approver_locator.inner_text()
        return {"success": True, "approver": approver_name}
    else:
        return {"success": False, "error": "Could not locate the Approving Manager element on the page."}
