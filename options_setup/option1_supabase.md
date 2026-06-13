# 🗄️ Option 1 Setup Guide: PostgreSQL & Supabase Integration

This guide provides step-by-step instructions to migrate your ISF-Core data layer from a local SQLite database to a robust PostgreSQL database using Supabase (either self-hosted via Docker or using the cloud platform).

## Why Upgrade to Supabase/PostgreSQL?
* **Enterprise Reliability:** Better concurrent write handling for multiple running micro-agents.
* **Database-Level Schedulers:** Native execution of tasks via extensions like `pg_cron`.
* **Security & Row-Level Access:** Role-based access control (RBAC) and Row-Level Security (RLS) policies.
* **Vector Capabilities:** Built-in support for `pg_vector` to store and query code embeddings.

---

## Step 1: Spin Up Supabase (Local Docker)

If you are self-hosting Supabase, use the pre-configured `supabase-docker` directory:

1. Navigate to the `supabase-docker` directory in your host system:
   ```bash
   cd supabase-docker
   ```
2. Copy the example environment variables:
   ```bash
   cp .env.sample .env
   ```
3. Boot the Supabase stack:
   ```bash
   docker compose up -d
   ```
4. Confirm all services (Kong, Postgres, Auth, Rest) are healthy:
   ```bash
   docker compose ps
   ```

---

## Step 2: Initialize Database Schema

Once your PostgreSQL instance is running, you must create the required tables for the orchestration engine. Run the following SQL migration script (located in your repository or run the block below in your Supabase SQL Editor):

```sql
-- Create scheduling table
CREATE TABLE IF NOT EXISTS cron_scheduled_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) UNIQUE NOT NULL,
    cron_expression VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL, -- 'HTTP_WEBHOOK', 'ISOLATED_PROCESS', 'SQL_FUNCTION'
    job_type VARCHAR(50) DEFAULT 'Cron_Daemon',
    target_payload_json JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    last_run_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create browser automation credentials table
CREATE TABLE IF NOT EXISTS browser_credentials (
    id SERIAL PRIMARY KEY,
    portal_name VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    encrypted_password TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default maintenance cron jobs
INSERT INTO cron_scheduled_jobs (job_name, cron_expression, target_type, job_type, target_payload_json)
VALUES 
('sonar-analysis-cleanup', '0 2 * * *', 'ISOLATED_PROCESS', 'Cron_Daemon', '{"module": "backend.tasks.sonar_cleaner"}'),
('morning-briefing-routine', '0 8 * * 1-5', 'ISOLATED_PROCESS', 'Cron_Daemon', '{"module": "backend.tasks.morning_briefing"}')
ON CONFLICT (job_name) DO NOTHING;
```

---

## Step 3: Configure Environment Variables

Update your `.env` file at the root of your `isf-core` directory to switch the database provider:

1. Open `.env`:
   ```bash
   nano .env
   ```
2. Disable SQLite and enable PostgreSQL / Supabase options:
   ```env
   # Database Configuration
   DB_PROVIDER=postgresql
   
   # PostgreSQL Connection Parameters
   DATABASE_URL=postgresql://postgres:your-super-secure-jwt-secret@localhost:54322/postgres
   
   # Supabase Client Credentials (Optional - for storage or Edge functions)
   SUPABASE_URL=http://localhost:8000
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here
   ```

---

## Step 4: Restart ISF-Core

Rebuild and restart your containers to apply the new database configuration:

```bash
docker compose down
docker compose up -d
```

Check logs to verify that the Nuitka engine successfully connects to your PostgreSQL instance:
```bash
docker compose logs -f isf-core-engine
```
