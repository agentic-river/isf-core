# 🌐 Option 6 Setup Guide: Browser Automation & Playwright Web Navigation (V3)

This guide outlines how to setup, configure, and use **Containerized Browser Automation (Playwright MCP)** in ISF-Core. This architecture equips your AI agents with virtual "hands" to log into external company web portals.

---

## 1. Setup (Containerized Execution)

In V3, the Playwright MCP server is fully containerized. It is published to Docker Hub at `agenticriver/playwright-mcp` and managed seamlessly alongside the rest of your stack. 

1. **Startup:** You can launch it using the dedicated compose file:
   ```bash
   docker compose -f compose.playwright-mcp.yml up -d
   ```
   This will pull the `agenticriver/playwright-mcp` image (e.g., tag `main`) from Docker Hub and launch it on port `8899`.

2. **Networking:** The container uses bridge networking and maps port `8899:8899`. The AI backend connects to the MCP server securely via `http://host.docker.internal:8899/sse`.

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

Once the container is running and credentials are in the vault, you can begin automating web tasks. The optimal workflow leverages the AI to do the heavy lifting:

### Step A: Site Discovery (Slow Path)
Use the Chat AI to manually explore the target site.
- **Prompt Example:** *"Go to example-portal.com, log in using my vault credentials, and figure out the exact DOM steps to export the monthly report. Take screenshots along the way."*
- The AI will use Playwright tools (`browser_navigate`, `browser_click`, `browser_snapshot`) to navigate the site, read the ARIA accessibility trees, and map out the process.

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
