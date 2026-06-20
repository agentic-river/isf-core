# 🗄️ Option 1 Setup Guide: PostgreSQL & Supabase Integration

This guide provides step-by-step instructions to migrate your ISF-Core data layer from a local SQLite database to a robust PostgreSQL database using Supabase (either self-hosted via Docker or using the cloud platform).

## Why Upgrade to Supabase/PostgreSQL?
* **Enterprise Reliability:** Better concurrent write handling for multiple running micro-agents.
* **Database-Level Schedulers:** Native execution of tasks via extensions like `pg_cron`.
* **Security & Row-Level Access:** Role-based access control (RBAC) and Row-Level Security (RLS) policies.
* **Vector Capabilities:** Built-in support for `pg_vector` to store and query code embeddings.

---

## Step 1: Clone Directly from Official Supabase (For Clean/Independent Deployments)
If you are installing Supabase from scratch on a new machine, you need to clone the official configuration files and copy them into your `isf-core` repository:

1. **Clone the official Supabase repository:**
   ```bash
   # Shallow clone the main repository
   git clone --depth 1 https://github.com/supabase/supabase
   ```

2. **Create the target directory inside isf-core and copy the Docker configurations:**
   ```bash
   # Ensure target directory exists
   mkdir -p isf-core/supabase-docker

   # Copy the docker files directly into the target folder
   cp -rf supabase/docker/. isf-core/supabase-docker/

   # Copy the environment template
   cp isf-core/supabase-docker/.env.example isf-core/supabase-docker/.env

   # Clean up the raw clone
   rm -rf supabase
   ```

3. **Navigate to the setup directory:**
   ```bash
   cd isf-core/supabase-docker
   ```

4. **Generate secure API keys, JWT secrets, and DB credentials:**
   These scripts will generate secure random credentials and insert them directly into your `.env` file:
   ```bash
   sh utils/generate-keys.sh
   sh utils/add-new-auth-keys.sh
   ```

5. **Set Studio Dashboard Credentials:**
   Open `.env` and set secure credentials for accessing the Supabase Studio UI:
   ```env
   # Edit DASHBOARD_USERNAME and DASHBOARD_PASSWORD
   DASHBOARD_USERNAME=admin
   DASHBOARD_PASSWORD=MustContainAtLeast1LetterAndSecure!
   ```

6. **Boot the Supabase stack:**
   ```bash
   docker compose up -d
   ```

7. **Confirm all services (Kong, Postgres, Auth, Rest) are healthy:**
   ```bash
   docker compose ps
   ```

---

## Step 2: Initialize Database Schema

Once your PostgreSQL instance is running, you must initialize the complete database schema for the ISF-Core platform.

The canonical schema definition script is located in your repository at:
📂 **`isf-core/supabase-docker/supabase_schema_init.sql`**  
*(Derived from the template source at `scaffold_templates/supabase-docker/supabase_schema_init.sql`)*

### How to Apply the Migration:

1. **Via Supabase Studio SQL Editor (Recommended):**
   * Access your Supabase Studio dashboard (by default at `http://localhost:3016` or your customized URL).
   * Log in using your `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`.
   * Click on the **SQL Editor** tab in the left sidebar.
   * Open `isf-core/supabase-docker/supabase_schema_init.sql` (or `./supabase_schema_init.sql` if in the docker folder) in any text editor, copy its entire contents, paste it into the Supabase SQL query box, and click **Run**.

2. **Via Command Line (using `psql` inside the Postgres container):**
   * If you prefer to execute the initialization via the command line, you can pipe the schema initialization script directly into the running container:
     ```bash
     docker exec -i supabase-db psql -U postgres -d postgres < isf-core/supabase-docker/supabase_schema_init.sql
     ```
     *(Note: If you run this command from within the `isf-core/supabase-docker/` directory itself, use `./supabase_schema_init.sql` as the path.)*

---

## Step 3: Configure Environment Variables

Update the main `.env` file at the root of your `isf-core` directory. The Docker Compose configuration (`compose.yml`) is set up to dynamically inject these variables into the agent orchestration containers, using `host.docker.internal` to route container-to-host traffic securely.

1. Open `.env` in the root of your `isf-core` directory:
   ```bash
   nano .env
   ```

2. Enable PostgreSQL / Supabase options by setting `DB_PROVIDER` and filling in the connection parameters using the secrets generated during your Supabase Docker setup (from `isf-core/supabase-docker/.env`):
   ```env
   # Database Configuration
   DB_PROVIDER=postgresql

   # Supabase & PostgreSQL Connection Parameters (Host-mapped)
   POSTGRES_PASSWORD=your_secure_db_password       # From jwt/key generation (postgres_password)
   POSTGRES_DB=postgres                            # Default DB name
   POSTGRES_PORT=5436                              # Default mapped external port for Postgres
   KONG_HTTP_PORT=8016                             # Default mapped external port for Kong API gateway
   ANON_KEY=your_supabase_anon_key_here            # From supabase-docker/.env (anon_key)
   SERVICE_ROLE_KEY=your_supabase_service_role_key # From supabase-docker/.env (service_role_key)
   ```

   > 💡 **Pro-Tip: Let the ISF-Core Agent Configure This for You!**
   > Instead of manually copy-pasting the keys and variables from your newly generated `supabase-docker/.env` file, you can instruct the ISF-Core agent to read the generated file and configure your main root `.env` file for you automatically.
   > 
   > **Copy & paste this prompt for the Agent:**
   > ```text
   > To setup supabase to isf-core in compose.yml, read the credentials and configurations inside `supabase-docker/.env` and update my main `.env` and compose.yml in the root directory. 
   > ```

3. **How This Works Under the Hood:**
   The platform's `compose.yml` automatically maps these variables so that your agent containers can resolve the database and API gateway services running on the host machine securely using:
   * **`SUPABASE_URL`** ➡️ `http://host.docker.internal:${KONG_HTTP_PORT}` (resolves to `http://host.docker.internal:8016`)
   * **`SUPABASE_KEY`** ➡️ `${SERVICE_ROLE_KEY}`
   * **`SUPABASE_DB_URL`** ➡️ `postgresql://postgres:${POSTGRES_PASSWORD}@host.docker.internal:${POSTGRES_PORT}/postgres` (resolves to `postgresql://postgres:...@host.docker.internal:5436/postgres`)

---

## Step 4: Restart ISF-Core

Rebuild and restart your containers to apply the new database configuration:

```bash
# at isf-core folder
docker compose down
docker compose up -d
```

Check logs to verify that the Nuitka engine successfully connects to your PostgreSQL instance:
```bash
# at isf-core folder
docker compose logs -f isf-core-engine
```
