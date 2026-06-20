# 🗄️ Option 5 Setup Guide: Federated AI Database Agent (db_agent)

This guide outlines how to leverage the **Federated AI Database Agent (`db_agent`)** in ISF-Core to inspect, query, and visualize your database tables, token metrics, and execution history using simple natural language instead of writing complex SQL.

## Why Use the Database Agent?

- **Zero SQL Barrier:** Query chat histories, job logs, or application tables by simply typing natural language questions.
- **Instant Visualizations:** Ask the agent to plot charts, and it will autonomously construct valid Vega-Lite charts displaying database growth or token utilization trends.
- **Federated Architecture:** Query vastly different dialects securely (PostgreSQL, MSSQL, SQLite, etc.) across different edge servers via API routing.

---

## Step 1: Deploy the DB Agent API Service

To enable the database agent edge functionality, you must run the `db_agent_api` microservice. Add the relevant block(s) below to your `docker-compose.yml` depending on your database engine.

### Option A: SQLite

For SQLite databases, you must mount the local directory containing your `.db` file so the container can access it.

```yaml
db_agent_api_sqlite:
  image: agenticriver/db-agent-api:main
  container_name: db_agent_api_sqlite
  ports:
    - "8501:8500" # Use a different host port if running alongside Postgres
  environment:
    # Use triple slashes for absolute paths inside the container
    - DATABASE_URL=sqlite:////data/my_database.db
    - DB_DIALECT=sqlite
    - QUERY_LIMIT=150
    - INTERNAL_API_KEY=${INTERNAL_API_KEY}
  volumes:
    # Mount the local ./data folder to /data inside the container
    - ./data:/data
  networks:
    - default
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8500/health || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Option B: PostgreSQL (Supabase Default)

```yaml
db_agent_api_supabase:
  image: agenticriver/db-agent-api:main
  container_name: db_agent_api_supabase
  ports:
    - "8500:8500"
  environment:
    # Connect directly to the 'db' container on port 5435 using native postgres protocol
    - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@supabase-db:${POSTGRES_PORT}/${POSTGRES_DB}
    - DB_DIALECT=postgres
    - QUERY_LIMIT=150
    - INTERNAL_API_KEY=${INTERNAL_API_KEY}
  networks:
    - default
    - supabase_shared_net
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8500/health || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
```

Run `docker compose up -d` to start the service(s).

---

## Step 2: Register the Database Node in the UI

Instead of using `.env` mappings, ISF-Core uses a dynamic `agent_nodes` registry managed securely through the web dashboard.

1. Open the ISF-Core Web Workspace (`http://localhost:3001`).
2. Navigate to the **DB Agent Admin** tab in the main navigation.
3. In the **Node Management** view, click **Add New Node**.
4. Configure the connection details:
   - **Node Name:** Give your database a recognizable name (e.g., `supabase-core` or `local-sqlite`).
   - **Dialect:** Select the correct engine (e.g., `PostgreSQL` or `SQLite`).
   - **API Endpoint:** Point it to the deployed DB Agent API (e.g., `http://db_agent_api_supabase:8500` or `http://db_agent_api_sqlite:8500` depending on the container name).
   - **Domain Description:** Provide a short description to help the AI Router know _when_ to use this database.
5. Save the Node.

---

## Step 3: Sync & Train the AI Schema Context

1. Switch to the **Schema Editor** tab inside the DB Agent Admin panel.
2. Click **Sync Schema Cache** to safely pull the raw physical table structures from the newly added node.
3. _(Optional)_ Run **Generate AI Semantics** to allow the system to sample the data and write human-readable data dictionaries into the system. This prevents the AI from hallucinating during complex queries.

---

## Step 4: Querying the Database Agent

You can now interact with the DB Agent directly from your Web Dashboard Chat:

- _"What was our total LLM token usage over the last 7 days? Show as a bar chart."_
- _"How many chat sessions are registered in the system?"_
- _"Search our job scheduler and list all cron tasks that failed recently."_

---

## 💡 Pro-Tips: Fine-Tuning AI Queries

If the Database Agent struggles with complex business logic or uses the wrong standard behavior when querying (e.g., misinterpreting status codes, using incorrect join paths, or filtering dates improperly), you can explicitly **fine-tune its behavior using rules**.

1. Navigate to the **Schema Editor** tab in the DB Agent Admin panel.
2. Locate the table(s) you want to tweak.
3. Click the **Add Rule** button for that specific table/schema.
4. Write a natural language override. 
   - *Example:* "When asked for 'active users', always filter where `status = 1` and `deleted_at IS NULL`."
   - *Example:* "If asked about 'revenue', always join the `billing` table and exclude refunded transactions."
5. Save the rule. The `db_agent` will instantly incorporate this rule as context in its prompt for future SQL generation, overriding its usual behavior!
