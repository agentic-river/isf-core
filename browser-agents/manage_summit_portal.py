from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
import os
import asyncio
import httpx
import aiofiles

IMAGE_PNG_MIME = "image/png"

class ManageSummitSchema(BaseModel):
    action: Literal["get_pending_approvals", "approve_requests"] = Field(
        ..., description="The action to perform on the Summit portal."
    )
    request_urls: Optional[List[str]] = Field(
        None, description="List of full URLs for the requests to approve. Required for 'approve_requests'."
    )
    comments: Optional[str] = Field(
        "Approved", description="Comments to add when approving."
    )

TASK_METADATA = {
    "name": "Summit_Portal",
    "description": "Performs actions on the Summit Web Portal: gets pending approval requests and approves them.",
    "domain": "ghds.mmh-global.com/SummitWeb",
    "schema": ManageSummitSchema
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
                files={"file": (filename, content, IMAGE_PNG_MIME)}
            )
            resp.raise_for_status()
            upload_data = resp.json()
        return upload_data.get("file_uri")
    except Exception as e:
        print(f"[Screenshot] Upload failed: {e}")
        return None

def _get_portal_url(credentials: Dict[str, Any]) -> str:
    domain = credentials.get('domain') or credentials.get('DOMAIN') or 'ghds.mmh-global.com/SummitWeb'
    if not domain.startswith('http'):
        portal_url = f"https://{domain}"
    else:
        portal_url = domain

    if not portal_url.endswith('/'):
        portal_url += '/'
    return portal_url

async def _handle_login(
    page: Page,
    context: BrowserContext,
    credentials: Dict[str, Any],
    session_path: str,
    session_dir: str
) -> Optional[Dict[str, Any]]:
    # Check if we need to login
    if "login" in page.url.lower() or await page.locator('#txtLogin').count() > 0:
        print("[Auth] Session expired or missing. Attempting login...")
        username = credentials.get('username') or credentials.get('USERNAME', '')
        password = credentials.get('password_encrypted') or credentials.get('password') or credentials.get('PASSWORD', '')

        if not username or not password:
            return {"success": False, "error": "Authentication failed. Missing username or password in vault."}

        await page.fill('#txtLogin', username)
        await page.fill('#txtPassword', password)

        async with page.expect_navigation(wait_until='networkidle'):
            await page.click('#butSubmit')

        if "login" in page.url.lower():
            return {"success": False, "error": "Authentication failed. Check credentials."}

        await asyncio.to_thread(os.makedirs, session_dir, exist_ok=True)
        await context.storage_state(path=session_path)
        print("[Auth] Session state saved successfully.")
    return None

async def _route_action(page: Page, inputs: ManageSummitSchema, portal_url: str) -> Dict[str, Any]:
    if inputs.action == "get_pending_approvals":
        return await _get_pending_approvals(page, portal_url)
    elif inputs.action == "approve_requests":
        if not inputs.request_urls:
            return {"success": False, "error": "request_urls is required for approve_requests"}
        return await _approve_requests(page, inputs.request_urls, inputs.comments)
    return {"success": False, "error": f"Unknown action: {inputs.action}"}

async def run_task(inputs: ManageSummitSchema, credentials: Dict[str, Any]) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-features=AsyncDns"])
        SESSION_DIR = '/app/backend/data/browser_sessions'
        session_path = os.path.join(SESSION_DIR, 'summit-web.json')

        has_session = await asyncio.to_thread(os.path.exists, session_path)
        context = await browser.new_context(
            storage_state=session_path if has_session else None,
            ignore_https_errors=True
        )
        page = await context.new_page()

        try:
            portal_url = _get_portal_url(credentials)
            print(f"[Navigate] Going to {portal_url}")
            await page.goto(portal_url, wait_until='networkidle')

            login_err = await _handle_login(page, context, credentials, session_path, SESSION_DIR)
            if login_err is not None:
                return login_err

            result = await _route_action(page, inputs, portal_url)
            if result.get("success"):
                file_uri = await _capture_and_upload_screenshot(page, "success")
                result["aria_snapshot"] = await _capture_aria_snapshot(page)
                result["file_uri"] = file_uri
                result["mime_type"] = IMAGE_PNG_MIME
            return result

        except PlaywrightTimeoutError as e:
            aria = await _capture_aria_snapshot(page)
            file_uri = await _capture_and_upload_screenshot(page, "error_timeout")
            return {"success": False, "error": f"Timeout Error: {str(e)}", "aria_snapshot": aria, "file_uri": file_uri, "mime_type": IMAGE_PNG_MIME}
        except Exception as e:
            aria = await _capture_aria_snapshot(page)
            file_uri = await _capture_and_upload_screenshot(page, "error_state")
            return {"success": False, "error": str(e), "aria_snapshot": aria, "file_uri": file_uri, "mime_type": IMAGE_PNG_MIME}
        finally:
            await browser.close()

def _write_file_sync(path: str, data: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)

async def _get_pending_approvals(page: Page, base_url: str) -> Dict[str, Any]:
    # Go to the base URL
    if page.url.lower() != base_url.lower():
        await page.goto(base_url, wait_until='networkidle')

    await page.wait_for_timeout(3000)

    # Save the whole HTML to a file so we can inspect it!
    html = await page.content()
    
    dump_path = os.path.join('/app/backend/data/browser_sessions', 'summit_dashboard_auth.html')
    await asyncio.to_thread(_write_file_sync, dump_path, html)

    return {"success": True, "data": [], "msg": "Dumped HTML"}

async def _approve_requests(page: Page, request_urls: List[str], comments: Optional[str]) -> Dict[str, Any]:
    comments = comments or "Approved"
    approved_count = 0
    results = []

    for url in request_urls:
        try:
            print(f"[Approve] Navigating to {url}")
            await page.goto(url, wait_until='networkidle')

            # Wait for form elements
            await asyncio.sleep(2)  # Give ASP.NET a moment to attach scripts

            # 1. Set all enabled Approval Dropdowns to "Yes" via evaluate
            # We use evaluate because they are select2 and hidden/disabled by asp.net
            await page.evaluate("""() => {
                const selects = document.querySelectorAll('select[id*="ddlApproval"]');
                let found = false;
                selects.forEach(s => {
                    if (!s.disabled) {
                        s.value = 'Yes';
                        // Trigger change for Select2 and ASP.NET postback/validation bindings
                        if (typeof jQuery !== 'undefined') {
                            jQuery(s).trigger('change');
                        } else {
                            s.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        found = true;
                    }
                });
                return found;
            }""")

            # 2. Add comments to enabled textareas
            await page.evaluate("""(comments) => {
                const textareas = document.querySelectorAll('textarea[id*="txtComments"]');
                textareas.forEach(t => {
                    if (!t.disabled) {
                        t.value = comments;
                    }
                });
            }""", comments)

            # 3. Click the Submit/Save button for Approvals (id*="btnApprovalSave")
            submit_btn = page.locator('input[id*="btnApprovalSave"], button[id*="btnApprovalSave"]').first
            if await submit_btn.count() > 0:
                print("[Approve] Found btnApprovalSave, triggering click via JS...")
                async with page.expect_navigation(wait_until='networkidle'):
                    await submit_btn.evaluate("el => el.click()")
                approved_count += 1
                results.append({"url": url, "status": "approved"})
            else:
                # Try generic save button if specific one is not found
                generic_save = page.locator('input[value="Submit"], button[value="Submit"]').first
                if await generic_save.count() > 0:
                    async with page.expect_navigation(wait_until='networkidle'):
                        await generic_save.click()
                    approved_count += 1
                    results.append({"url": url, "status": "approved (generic button)"})
                else:
                    results.append({"url": url, "status": "failed - no submit button found"})
        except Exception as e:
             results.append({"url": url, "status": f"failed - {str(e)}"})

    return {"success": True, "approved_count": approved_count, "details": results}
