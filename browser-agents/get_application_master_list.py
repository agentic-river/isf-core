import os
import json
import httpx
import aiofiles
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from playwright.async_api import async_playwright, Page

PNG_MIME_TYPE = "image/png"

class GetApplicationMasterListSchema(BaseModel):
    pass

TASK_METADATA = {
    "name": "ITSM_get_application_master_list",
    "description": "Fetches the Application Master list from the ITSM portal. This retrieves application configuration data such as workgroups and PICs.",
    "domain": "https://e1app.mmh-global.com/ITSM/auth",
    "schema": GetApplicationMasterListSchema
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
        async with aiofiles.open(path, "rb") as f:
            content = await f.read()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                proxy_url,
                files={"file": (filename, content, PNG_MIME_TYPE)}
            )
            resp.raise_for_status()
            upload_data = resp.json()
        return upload_data.get("file_uri")
    except Exception as e:
        print(f"[Screenshot] Upload failed: {e}")
        return None


async def _login_if_needed(page: Page, context: Any, credentials: Dict[str, Any], session_path: str) -> None:
    """
    Perform login if the user is redirected to the auth screen or if credentials inputs are visible.
    """
    if "ITSM/auth" in page.url or await page.locator("input[name='username']").count() > 0:
        print("Logging in...")
        username = credentials.get("username") or credentials.get("USERNAME", "")
        password = credentials.get("password_encrypted") or credentials.get("password") or credentials.get("PASSWORD", "")

        await page.fill("input[name='username'], input[type='text'], input[formcontrolname='username']", username)
        await page.fill("input[name='password'], input[type='password'], input[formcontrolname='password']", password)
        await page.click("button[type='submit'], button:has-text('Login')")
        await page.wait_for_timeout(5000)

        await context.storage_state(path=session_path)

        # Navigate directly to the Application Master List view
        if "itsm/master/project" not in page.url:
            await page.goto("https://e1app.mmh-global.com/ITSM/itsm/master/project", wait_until="networkidle")


async def _set_page_size_to_100(page: Page) -> None:
    """
    Set the table page size to 100 using the combobox so that all records fit in one page.
    """
    page_size_changed = False
    try:
        combo = page.get_by_role("combobox", name="items per page").first
        if await combo.is_visible(timeout=5000):
            await combo.click()
            await page.wait_for_timeout(1000)

            option = page.get_by_role("option", name="100").first
            if not await option.is_visible(timeout=1000):
                option = page.locator("mat-option, [role='option'], option").filter(has_text="100").first

            if await option.is_visible(timeout=2000):
                await option.click()
                page_size_changed = True
                print("[PageSize] Successfully selected 100 from ARIA combobox.")
    except Exception as e:
        print(f"[PageSize] ARIA combobox strategy failed: {e}")

    if page_size_changed:
        await page.wait_for_timeout(2000)
        try:
            await page.wait_for_selector("table tr td", timeout=10000)
        except Exception:
            await page.wait_for_load_state("networkidle", timeout=10000)


async def _extract_table_data(page: Page) -> List[Dict[str, str]]:
    """
    Extract the application details from the data table.
    """
    await page.wait_for_selector("tr", timeout=15000)

    await _set_page_size_to_100(page)

    data = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('table tr'))
            .filter(tr => tr.querySelector('td') !== null)
            .map(tr => {
                const cells = Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
                return {
                    "Application Code": cells[0] || "",
                    "Application Name": cells[1] || "",
                    "Workgroup": cells[2] || "",
                    "PIC": cells[3] || "",
                    "Environment": cells[4] || "",
                    "Path": cells[5] || ""
                };
            })
            .filter(row => row["Application Code"].length > 0);
    }''')
    print(f"[Extraction] Retrieved {len(data)} applications in a single page")
    return data


async def run_task(inputs: GetApplicationMasterListSchema, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fast Path automation script to fetch the Application Master List.
    Navigates to the ITSM project master and extracts the data table.
    """
    print(f"Starting get_application_master_list with inputs: {inputs}")

    username = credentials.get("username") or credentials.get("USERNAME", "")
    password = credentials.get("password_encrypted") or credentials.get("password") or credentials.get("PASSWORD", "")

    if not username or not password:
        return {
            "status": "error",
            "message": "Missing credentials in vault for domain https://e1app.mmh-global.com/ITSM/auth"
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-features=AsyncDns"])
        try:
            SESSION_DIR = '/app/backend/data/browser_sessions'
            os.makedirs(SESSION_DIR, exist_ok=True)
            session_path = os.path.join(SESSION_DIR, f"{TASK_METADATA['name']}.json")

            state_exists = os.path.exists(session_path) and os.path.getsize(session_path) > 0

            context = await browser.new_context(
                storage_state=session_path if state_exists else None,
                ignore_https_errors=True
            )
            page = await context.new_page()

            await page.goto("https://e1app.mmh-global.com/ITSM/itsm/master/project", wait_until="networkidle")
            await page.wait_for_timeout(5000)

            await _login_if_needed(page, context, credentials, session_path)

            data = await _extract_table_data(page)

            file_uri = await _capture_and_upload_screenshot(page, "success")
            json_str = json.dumps(data, indent=2)

            return {
                "status": "success",
                "message": f"Successfully retrieved {len(data)} applications.\n\n```json\n{json_str}\n```",
                "data": data,
                "aria_snapshot": await _capture_aria_snapshot(page),
                "file_uri": file_uri,
                "mime_type": PNG_MIME_TYPE
            }

        except Exception as e:
            aria = await _capture_aria_snapshot(page)
            file_uri = await _capture_and_upload_screenshot(page, "error_state")
            return {
                "status": "error",
                "message": str(e),
                "aria_snapshot": aria,
                "file_uri": file_uri,
                "mime_type": PNG_MIME_TYPE
            }
        finally:
            await browser.close()
