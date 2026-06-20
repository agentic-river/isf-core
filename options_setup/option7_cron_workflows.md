# ⏰ Option 7 Setup Guide: Background Automation (Cron-Scheduled Workflows)

This guide provides instructions to schedule, manage, and run automated background jobs (such as morning dossiers, code-cleanups, static analysis, and self-healing test runs) using the built-in Cron Services architecture.

## Why Setup Cron Workflows?

- **Hands-off Development:** Run continuous code scans, check for compilation smells, and fix tests in the background while away from your computer.
- **Routine Information Aggregation:** Receive a compiled markdown dossier of your unread emails and upcoming calendar meetings every weekday morning.
- **Continuous Integration:** Trigger custom scripts to build, compile, and push artifacts on scheduled calendar releases.

---

## 1. The Scheduling Architecture (Dual-Dimension Model)

The scheduling architecture separates the execution engine from the target payload. Every job requires two specific configurations:

### A. Execution Engines (`job_type`)

- **`Cron_Daemon`**: Managed by the local FastAPI background thread. Best for standard application tasks, running local python scripts, and triggering webhooks.
- **`PG_CRON`**: Managed entirely by PostgreSQL's native `pg_cron` extension. Best for database housekeeping and high-availability core tasks that must run reliably even if the python server is down.

### B. Target Actions (`target_type`)

- **`HTTP_WEBHOOK`**: Fires an HTTP request (POST/GET etc.) to a configured URL. Supported by both `Cron_Daemon` and `PG_CRON`.
- **`ISOLATED_PROCESS`**: Spawns a secure, isolated OS subprocess running a Python script under the `backend/tasks/` folder. Protects the main app from memory leaks. Supported by `Cron_Daemon`.
- **`SQL_FUNCTION`**: Executes a native PostgreSQL PL/pgSQL database procedure directly. Supported by `PG_CRON`.

---

## 2. Managing Jobs via the UI Dashboard

You don't need to write manual database scripts to view or manage jobs. The application provides a dedicated **Cron Job Dashboard** in the Web UI:

- **Verify Settings & Status**: View all registered jobs, their intervals, and current status (`Idle`, `Running`, `Error`).
- **Enable/Disable**: Easily toggle jobs on or off without deleting them via the UI switches.
- **Execution History**: Click on a job to view detailed logs, duration, and telemetry payloads from previous runs.
- **Run Now**: Manually trigger a job immediately for testing or out-of-schedule execution.

---

## 3. Registering & Editing Jobs (The AI-Assisted Workflow)

The most efficient way to create or edit scheduled tasks is to **ask the AI Chat Agent**!

**🤖 AI Agent Directive:** When an AI agent is requested to manage, edit, or create cron workflows, it **MUST** strictly read and adhere to the protocol documented in `@rules/Cron_Service_and_Job_Scheduling_Spec.md` before executing the `register_cron_job` tool or creating background scripts.

The AI agent has a dedicated system tool (`register_cron_job`) that allows it to automatically configure the task, validate the schema, insert it into the database, and trigger a live synchronization reload so it appears in your Dashboard instantly.

### Examples of what you can ask the AI:

- _"Use Cron Service rule, create a new daily job at 8am that runs the `backend.tasks.morning_briefing` script as an isolated process."_
- _"Explain the cron workflow for the `auto_agent_task` job currently registered."_
- _"Update the cron schedule for my code-cleanup job to run every 3 hours."_

---

## 4. Writing Custom Background Scripts (`ISOLATED_PROCESS`)

If you want the AI to write and schedule a custom Python maintenance routine:

1. Have the AI create the python script strictly inside the `backend/tasks/` folder (e.g., `backend/tasks/my_custom_cleanup.py`).
2. Ensure the script prints its final output using the JSON protocol:
   ```python
   def run_task():
       print("Starting workspace optimization...")
       # Your logic here
       print('__CRON_RESULT__ {"status": "SUCCESS", "message": "Cleanups completed", "duration_ms": 120, "response_payload": {}, "error_message": null}')
   ```
3. Ask the AI to register it: _"Register my new custom cleanup script to run every Sunday at midnight."_
