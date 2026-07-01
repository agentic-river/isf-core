# 🌐 Option 6 Setup Guide: Browser Automation & Playwright Web Navigation (V2)

This guide outlines how to setup, configure, and use **Host-Native Browser Automation (Playwright MCP)** in ISF-Core. This architecture equips your AI agents with virtual "hands" to log into external company web portals and bypass Docker networking hurdles to access local dev servers.

---

## 1. Setup (Host-Native Execution)

ISF-Core V2 moved away from a containerized browser to a Host-Native MCP Server. You MUST run the daemon natively on your host machine alongside your Docker containers so the browser can access your local VPNs and `localhost` servers.

1. **Create the Virtual Environment:** Ensure your Python environment is set up on the host:
   ```bash
   uv venv
   uv pip sync requirements.txt
   ```
2. **Start the Playwright MCP Server:** Use the provided startup script:
   ```bash
   ./start_playwright_mcp_server.sh
   ```
   This will launch the Playwright MCP server (running `ai_manager/playwright_mcp.py`) natively on your host machine on port 8899, which the backend connects to via `http://host.docker.internal:8899/sse`.

---

## 2. Configure (Credentials Management)

To let the agent log into external portals on your behalf, credentials must be securely stored in the system's Vault (`browser_credentials` table). 

The easiest and recommended way to manage this is directly through the Chat UI:

1. **Ask the AI:** Instruct the Chat AI to insert or update the credentials for you. 
   - *Example:* "Save my browser credentials for 'example-portal.com' with username 'my_id' and my password."
2. **Verify Registration:** 
   - Open your Web Dashboard (`http://localhost:3001`).
   - Navigate to the **Browser Agent Dashboard -> Vault** to visually confirm the domain and username are registered.
   - Alternatively, you can ask the AI to query the `browser_credentials` database table directly to ensure the setup is correct.

---

## 3. Usage (The Discovery & Fast-Track Workflow)

Once the server is running and credentials are in the vault, you can begin automating web tasks. The optimal workflow leverages the AI to do the heavy lifting:

### Step A: Site Discovery (Slow Path)
Use the Chat AI to manually explore the target site.
- **Prompt Example:** *"Go to example-portal.com, log in using my vault credentials, and figure out the exact DOM steps to export the monthly report. Take screenshots along the way."*
- The AI will use Host-Native Playwright tools (`browser_navigate`, `browser_click`, `browser_snapshot`) to navigate the site, read the ARIA accessibility trees, and map out the process.

### Step B: Generate the "Fast Track" Script
Once the AI successfully navigates the workflow in Discovery Mode, instruct it to write a permanent script.
- **Prompt Example:** *"Now that you know how the site works, use the rule `@rules/Agentic_Browser_Automation_V2_Guide.md` to write a Fast Track Python script in the `browser-agents/` directory."*
- **For the AI Agent:** The AI MUST ALWAYS refer to the strict guidelines defined in `@rules/Agentic_Browser_Automation_V2_Guide.md` when writing or updating browser automation scripts. This ensures the script inherits `BrowserAgent`, handles `asyncio` correctly, uses `get_credentials`, and captures traces properly.
- The AI will generate a highly optimized, resilient Python script utilizing the `BrowserAgent` base class, complete with secure credential injection and error handling.

### Step C: Instant Execution
Once the script is saved in the `browser-agents/` folder, the backend dynamically discovers it. 
Future requests (e.g., *"Export my monthly report"*) will bypass the slow Discovery Mode and instantly execute your new Fast Track script in the background!

### Step D: Schedule Automated Execution (Cron Jobs)
Once you have generated your "Fast Track" script, you can schedule it to run automatically on a regular interval (e.g., daily at 8 AM). 
- Instruct the AI to set up a scheduled task for your browser script.
- *Prompt Example:* "Schedule my monthly report browser agent to run on the 1st of every month at 9 AM."
- **For the AI Agent:** When setting up cron jobs, the AI MUST refer to the strict guidelines defined in `@rules/Cron_Service_and_Job_Scheduling_Spec.md`. This rule dictates how to properly use the `register_cron_job` tool to configure the execution engine and target protocol.