# 🌐 Option 6 Setup Guide: Browser Automation & Playwright Web Navigation

This guide outlines how to configure **Browser Automation (Playwright headless Chrome)** in ISF-Core. This equips your AI agents with virtual "hands" to log into external company web portals, parse leave balances, schedule calendar appointments, or approve pending requests.

## Why Enable Browser Automation?
* **Legacy System Bridges:** Many legacy enterprise tools (like eLeave or Summit) lack functional APIs. Browser automation bridges this gap by letting the AI navigate pages exactly like a human would.
* **Complex UI Workflows:** Agents can perform multi-step web processes, such as downloading reports, filling forms, and filing IT tickets.
* **Visual Audit Logs:** At every step of a browser run, the agent captures screenshots and console logs, storing them securely in your workspace so you can audit the actions visually.

---

## Step 1: Verify Chrome/Playwright Container Status

ISF-Core includes a dedicated headless browser container running alongside the engine. Ensure your `docker-compose.yml` includes the browser runner service:

1. Look for the `browser-agent` block in your `docker-compose.yml`:
   ```yaml
   browser-agent:
     image: mcr.microsoft.com/playwright:v1.40.0-focal
     ports:
       - "8899:8899"
     environment:
       - PORT=8899
   ```
2. Confirm the service is running:
   ```bash
   docker compose ps browser-agent
   ```

---

## Step 2: Encrypt & Store Portal Credentials

To let the agent log into external portals on your behalf, you must save credentials in the `browser_credentials` table (which is fully encrypted locally):

1. Open your Web Dashboard (`http://localhost:3001`).
2. Go to the **Credentials Manager** or run an interactive SQL query to store credentials securely:
   ```sql
   INSERT INTO browser_credentials (portal_name, username, encrypted_password)
   VALUES ('eLeave_Portal', 'your_employee_id', 'AES_ENCRYPTED_PASSWORD_HERE');
   ```

---

## Step 3: Triggering Browser Agents

You can invoke browser agents directly via the chat dashboard or delegate them to background cron jobs:

1. **Ask Chat:**
   > *"Navigate to eLeave portal and pull my annual leave balance."*
2. **Execution Flow:**
   * The orchestration engine calls the `eLeave_Portal` module.
   * Playwright launches a headless browser, navigates to the login screen, decrypts and injects your credentials, and navigates to the balance page.
   * The agent parses the DOM text, captures a screenshot, closes the browser, and replies: *"You have 14 days of Annual Leave remaining (screenshot attached)."*
