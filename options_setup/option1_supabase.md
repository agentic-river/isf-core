# 🗄️ Option 1 Setup Guide: PostgreSQL & Supabase Integration

This guide provides step-by-step instructions to migrate your ISF-Core data layer from a local SQLite database to a robust PostgreSQL database using Supabase.

## Step 1: Clone Directly from Official Supabase (For Clean/Independent Deployments)

1. **Clone Supabase 1 level above the target directory (e.g., `my-ai-project`):**
   ```bash
   cd ..
   git clone --depth 1 https://github.com/supabase/supabase
   ```

2. **Copy the Supabase docker template to the target directory's `supabase-docker` subfolder:**
   ```bash
   mkdir -p my-ai-project/supabase-docker
   cp -rf supabase/docker/. my-ai-project/supabase-docker/
   cp my-ai-project/supabase-docker/.env.example my-ai-project/supabase-docker/.env
   ```

3. **Go to the target dir/supabase-docker folder then run the Generate secure API keys, JWT secrets, and DB credentials:**
   ```bash
   cd my-ai-project/supabase-docker
   sh utils/generate-keys.sh
   sh utils/add-new-auth-keys.sh
   ```

4. **Boot the Supabase stack:**
   ```bash
   docker compose up -d
   ```

5. **Confirm all services (Kong, Postgres, Auth, Rest) are healthy:**
   ```bash
   docker compose ps
   ```

6. **Clean up the raw clone supabase:**
   ```bash
   # Navigate back to the directory where the raw supabase repo was cloned
   cd ../..
   rm -rf supabase
   ```

## Step 2: Initialize Database Schema

Once your PostgreSQL instance is running, you must initialize the complete database schema. 

1. **Locate the schema initialization script:**
   The script is located at: `github_isf_core/supabase-migrations/supabase_schema_init.sql`

2. **Apply the schema:**
   * **Via Supabase Studio (Recommended):** 
     Access your Supabase dashboard at `http://localhost:8000`, log in, navigate to the **SQL Editor**, paste the entire contents of `github_isf_core/supabase-migrations/supabase_schema_init.sql`, and click **Run**. [for login credential: refer to supabase-docker/.env - DASHBOARD_USERNAME / DASHBOARD_PASSWORD]
   * **Via Command Line:**
     Run the following command to pipe the schema directly into your running database container:
     ```bash
     docker exec -i supabase-db psql -U postgres -d postgres < github_isf_core/supabase-migrations/supabase_schema_init.sql
     ```
3. **Add Six Cron Scheduled Jobs:**
   * Access your Supabase dashboard at `http://localhost:8000`, log in, navigate to the **SQL Editor**, paste the entire contents of `github_isf_core/supabase-migrations/migration_to_supabase.sql`, and click **Run**. 

## Step 3: Configure Environment Variables (.env)

Update the main `.env` file at the root of your target directory (e.g., `my-ai-project`).

1. **Open the root `.env` file:**
   ```bash
   # Navigate to your project root
   cd my-ai-project
   ```

2. **Configure Database Parameters:**
   Copy the credentials that were generated in `my-ai-project/supabase-docker/.env` and paste them into your root `.env` file:
   ```env
   # Supabase & PostgreSQL Connection Parameters
   POSTGRES_PASSWORD=your_secure_db_password       # From supabase-docker/.env (POSTGRES_PASSWORD)
   JWT_SECRET=cDXz...                              # From supabase-docker/.env (JWT_SECRET)
   ANON_KEY=your_supabase_anon_key_here            # From supabase-docker/.env (ANON_KEY)
   SERVICE_ROLE_KEY=your_supabase_service_role_key # From supabase-docker/.env (SERVICE_ROLE_KEY)
   ```
   *(💡 **Pro-Tip:** You can just ask the AI agent to read `supabase-docker/.env` and automatically configure your main `.env` file for you!)*

## Step 4: Restart ISF-Core

Rebuild and restart your containers to apply the new database configuration.

1. **Restart the stack:**
   ```bash
   # Ensure you are in your project root (e.g., my-ai-project)
   python shutdown_isf_core.py
   python start_isf_core.py
   ```

2. **Verify successful connection:**
   Open the System Healthy UI, enabled the Supabase (at Core Infrastructure Health)

