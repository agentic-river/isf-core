# 🗄️ Option 5 Setup Guide: Federated AI Database Agent (db_agent)

This guide outlines how to leverage the **Federated AI Database Agent (`db_agent`)** in ISF-Core to inspect, query, and visualize your local workspace tables, token metrics, and execution history using simple natural language instead of writing complex SQL.

## Why Use the Database Agent?
* **Zero SQL Barrier:** Query local chat histories, job logs, or user tables by simply typing natural language questions.
* **Instant Visualizations:** Ask the agent to plot charts, and it will autonomously construct valid Vega-Lite charts displaying database growth or token utilization trends.
* **Secured Connections:** Protects your underlying data using secure connection mappings and parameterized queries to block SQL injection attempts.

---

## Step 1: Map Databases in Workspace

By default, the AI Database Agent automatically maps and reads:
* Your primary workspace database: `data/chat_history.db` (SQLite)
* The background scheduler database: `data/scheduler.db` (SQLite) or your PostgreSQL Supabase connection (if Option 1 is active).

If you want the agent to connect to additional databases:
1. Copy your database file (e.g., `my_analytics.db`) into the `data/` folder.
2. Open your `.env` file:
   ```bash
   nano .env
   ```
3. Register your database mapping parameter:
   ```env
   # Add federated DB paths separated by commas
   FEDERATED_DB_PATHS=data/chat_history.db,data/scheduler.db,data/my_analytics.db
   ```

---

## Step 2: Querying the Database Agent

You can interact with the DB Agent directly from your Web Dashboard Chat or via automated background tasks:

1. Open the ISF-Core Web Workspace (`http://localhost:3001`).
2. Ask questions such as:
   * *"What was our total LLM token usage over the last 7 days? Show as a bar chart."*
   * *"How many chat sessions are registered in the system?"*
   * *"Search our job scheduler and list all cron tasks that failed recently."*

---

## Step 3: Understanding the Data Output

* **Tabular Data:** If the result is a standard table, the dashboard renders it in a responsive, sortable data grid.
* **Vega-Lite Charts:** If you request a visual representation (e.g., *"Plot daily token cost as a line chart"*), the DB Agent returns a raw Vega-Lite specification that renders inside your UI.
