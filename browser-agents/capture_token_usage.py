import asyncio
import os
import base64
import httpx
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

IMAGE_PNG_MIME_TYPE = "image/png"


class CaptureTokenUsageSchema(BaseModel):
    url: str = Field(default="http://localhost:3001", description="The URL of the application to capture.")
    output_dir: str = Field(default="tmp", description="Directory to save screenshots.")


TASK_METADATA = {
    "name": "capture_token_usage",
    "description": "Navigates to the token usage dashboard and captures 3 screenshots: Main View, MTD Chart, and Detailed View.",
    "schema": CaptureTokenUsageSchema
}


async def _capture_aria_snapshot_via_mcp() -> str:
    """
    Capture the ARIA accessibility tree via the MCP browser_snapshot tool.

    NOTE: This requires the Playwright MCP server to be online.
    For offline-resilient ARIA snapshots, use the direct Playwright helper
    (_capture_aria_snapshot) available in Layer 3 scripts.

    Returns a compact semantic YAML-like representation of the page.
    """
    from backend.core.mcp_manager import mcp_manager
    try:
        result = await mcp_manager.execute_tool("playwright", "browser_snapshot", {})
        if isinstance(result, str):
            return result
        if hasattr(result, 'content') and result.content:
            return str(result.content[0].text)
        return str(result) if result else ""
    except Exception as e:
        print(f"[ARIA] MCP snapshot failed: {e}")
        return ""


def _read_file_sync(filepath: str) -> bytes:
    """
    Synchronously read a file as bytes.
    """
    with open(filepath, "rb") as f:
        return f.read()


async def _upload_screenshot_to_proxy(filepath: str) -> Optional[str]:
    """
    Upload a local screenshot file to the AI proxy and return a file_uri
    for multimodal vision ingestion by the AI agent.
    """
    filename = os.path.basename(filepath)
    proxy_url = f"{os.getenv('AI_PROXY_URL', 'http://localhost:8080')}/v1/upload"
    try:
        # Read the file bytes asynchronously in a separate thread to avoid blocking the event loop
        file_bytes = await asyncio.to_thread(_read_file_sync, filepath)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                proxy_url,
                files={"file": (filename, file_bytes, IMAGE_PNG_MIME_TYPE)}
            )
            resp.raise_for_status()
            upload_data = resp.json()
        return upload_data.get("file_uri")
    except Exception as e:
        print(f"[Screenshot] Upload failed: {e}")
        return None


def _save_image_data_sync(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)


async def _wait_for_react_ready(mcp_manager: Any) -> None:
    """
    Wait for React to mount and the app to be ready (specifically the 'MTD Cost' text).
    """
    print("Waiting for 'MTD Cost' to appear...")
    try:
        await asyncio.wait_for(
            mcp_manager.execute_tool("playwright", "browser_wait_for", {"selector": "text=MTD Cost", "timeout": 20000}),
            timeout=25.0
        )
    except Exception as e:
        print(f"Wait for 'MTD Cost' failed/timed out: {e}. Taking screenshot anyway.")


async def _focus_token_usage_chart(mcp_manager: Any) -> None:
    """
    Click the chart container (now focusable via tabIndex) to set focus for PageDown.
    """
    try:
        print("Targeting focused chart container...")
        await mcp_manager.execute_tool("playwright", "browser_click", {"selector": "[data-testid=\"token-usage-chart\"]", "timeout": 5000})
    except Exception as e:
        print(f"Focus click on [data-testid=\"token-usage-chart\"] failed: {e}. Trying fallback...")
        try:
            await mcp_manager.execute_tool("playwright", "browser_click", {"selector": ".vega-embed", "timeout": 5000})
        except Exception as e2:
            print(f"Fallback focus click failed: {e2}. Proceeding with PageDown anyway.")


async def _save_screenshots(output_dir: str, screenshots: List[Any]) -> List[str]:
    """
    Decodes and saves screenshots to the specified output directory.
    """
    results: List[str] = []
    for i, res in enumerate(screenshots, 1):
        if res and not getattr(res, "isError", False) and hasattr(res, 'content') and res.content:
            try:
                img_data = base64.b64decode(res.content[0].text)
                path = f"{output_dir}/screenshot_{i}.png"
                await asyncio.to_thread(_save_image_data_sync, path, img_data)
                results.append(path)
                print(f"Saved {path} ({len(img_data)} bytes)")
            except Exception as b64e:
                print(f"Failed to decode screenshot {i}: {b64e}")
        else:
            print(f"Screenshot {i} result was invalid: {res}")
    return results


async def run_task(inputs: CaptureTokenUsageSchema, credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Automated workflow to capture token usage screenshots.
    Bypasses UI interaction for high-reliability snapshots.
    """
    _ = credentials  # Keep for signature compatibility
    from backend.core.mcp_manager import mcp_manager

    # Ensure MCP is initialized
    await mcp_manager.initialize()

    url = inputs.url
    output_dir = inputs.output_dir
    os.makedirs(output_dir, exist_ok=True)

    results: List[str] = []

    try:
        # 1. Navigate
        print(f"Navigating to {url}...")
        await mcp_manager.execute_tool("playwright", "browser_navigate", {"url": url})

        # 2. Wait for React to mount and the app to be ready
        await _wait_for_react_ready(mcp_manager)

        # Extra buffer
        await asyncio.sleep(5)

        # Take initial screenshot
        print("Taking initial screenshot...")
        res1 = await mcp_manager.execute_tool("playwright", "browser_take_screenshot", {})

        # 3. Click MTD Cost to show Token Usage UI
        print("Clicking MTD Cost...")
        await mcp_manager.execute_tool("playwright", "browser_click", {"selector": "text=MTD Cost"})

        # 4. Wait for the token usage modal/container
        await asyncio.sleep(5)
        print("Taking chart screenshot...")
        res2 = await mcp_manager.execute_tool("playwright", "browser_take_screenshot", {})

        # 5. Page Down for detailed view
        print("Scrolling down...")
        # Click the chart container (now focusable via tabIndex) to set focus for PageDown
        await _focus_token_usage_chart(mcp_manager)

        await mcp_manager.execute_tool("playwright", "browser_press_key", {"key": "PageDown"})
        await asyncio.sleep(2)
        res3 = await mcp_manager.execute_tool("playwright", "browser_take_screenshot", {})

        # Save results
        results = await _save_screenshots(output_dir, [res1, res2, res3])

        # Upload last successful screenshot for visual confirmation
        file_uri = None
        if results:
            file_uri = await _upload_screenshot_to_proxy(results[-1])
        aria = await _capture_aria_snapshot_via_mcp()
        return {"status": "success", "files": results, "aria_snapshot": aria, "file_uri": file_uri, "mime_type": IMAGE_PNG_MIME_TYPE}

    except Exception as e:
        print(f"Token capture failed: {e}")
        # Try to upload whatever we have
        file_uri = None
        if results:
            file_uri = await _upload_screenshot_to_proxy(results[-1])
        aria = await _capture_aria_snapshot_via_mcp()
        return {"status": "error", "detail": str(e), "aria_snapshot": aria, "file_uri": file_uri, "mime_type": IMAGE_PNG_MIME_TYPE}
