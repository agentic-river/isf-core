# ⏰ Option 7 Setup Guide: Background Automation (Cron-Scheduled Workflows)

This guide provides instructions to schedule and run automated background jobs (such as morning dossiers, code-cleanups, static analysis, and self-healing test runs) using the built-in ISF-Core Cron Daemon.

## Why Setup Cron Workflows?
* **Hands-off Development:** Run continuous code scans, check for compilation smells, and fix tests in the background while away from your computer.
* **Routine Information Aggregation:** Receive a compiled markdown dossier of your unread emails and upcoming calendar meetings every weekday morning.
* **Continuous Integration Integration:** Trigger custom scripts to build, compile, and push artifacts on scheduled calendar releases.

---

## Step 1: Understand the Scheduling Architecture

ISF-Core operates a background scheduler thread that constantly checks the database table `cron_scheduled_jobs`.
Every job entry consists of:
* `job_name`: A unique identifier for the automated task.
* `cron_expression`: Standard 5-field cron syntax (e.g., `0 * * * *` for hourly).
* `target_payload_json`: Key-value JSON mapping that specifies the python module or API endpoint to trigger.

---

## Step 2: Register a Scheduled Task

You can insert or update scheduled background tasks directly through the interactive Web Dashboard or by writing a database insert script:

```sql
-- Register a daily morning briefing task at 8:00 AM on weekdays
INSERT INTO cron_scheduled_jobs (job_name, cron_expression, target_type, target_payload_json)
VALUES (
    'morning-dossier-alert', 
    '0 8 * * 1-5', 
    'ISOLATED_PROCESS', 
    '{"module": "backend.tasks.morning_briefing"}'
)
ON CONFLICT (job_name) 
DO UPDATE SET cron_expression = EXCLUDED.cron_expression;
```

---

## Step 3: Write a Custom Background Task Script

If you want to run a custom Python maintenance routine:

1. Create your python script inside the `backend/tasks/` folder (e.g., `backend/tasks/my_custom_cleanup.py`):
   ```python
   def run_task():
       # Your custom cleaning logic here
       print("Starting workspace optimization...")
       # Delete obsolete lock files, clean temp folders, run test commands
       print("Cleanups completed successfully.")
   ```
2. Register the task in the database, mapping it to your newly created file:
   ```json
   {"module": "backend.tasks.my_custom_cleanup"}
   ```

---

## Step 4: Monitor Cron Logs

The cron logs run in real-time inside your main engine thread. To verify execution:

```bash
docker compose logs -f isf-core-engine | grep -i "cron"
```
Or view execution history and logs directly under the **Scheduler** tab inside your interactive Web Dashboard UI!
