# 🔑 Option 10: AI Proxy Virtual Keys & Token Spend Tracking

Assign individual virtual developer keys to your team members, track token consumption per project in real-time, and export granular billing reports — all without touching the frontend.

---

## 📋 Prerequisites

- ISF-Core already running with `ai-proxy` container
- Python 3.12+ installed on your host
- Admin access to the project root

---

## Step 1: Enable the Feature Flag

Open your `.env` file (at the project root) and add:

```bash
ENABLE_VIRTUAL_KEY=true
```

If the line is missing or set to `false`, the virtual key system is completely disabled and the proxy runs with zero overhead (current default behavior).

---

## Step 2: Generate a Virtual Key for a Developer

Use the Admin CLI tool inside the container:

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py generate <username> --project <project_name>
```

**Example:**

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py generate dev_john --project project_alpha
```

**Output:**

```
✅ Key generated for dev_john/project_alpha:
   Key:    sk-virt-a1b2c3d4e5f6...
   Status: active
   Created: 2025-01-15T10:00:00Z

⚠️  Copy this key now — it is not stored in plaintext anywhere else.
```

> 💡 **One developer, multiple projects:** Run the command again with a different `--project` to generate additional keys for the same developer.

---

## Step 3: Restart the AI Proxy

Rebuild and restart the `ai-proxy` container to pick up the flag and the newly generated key index:

```bash
docker compose up -d --build ai-proxy
```

Verify the proxy loaded the key index:

```bash
docker compose logs ai-proxy | grep "Virtual key index"
```

You should see:

```
[INFO] proxy: Virtual key index loaded: 1 active keys
```

---

## Step 4: Configure the Developer's Environment

The developer adds their virtual key to their project's `.env` file:

```bash
AI_PROXY_VIRTUAL_KEY=sk-virt-a1b2c3d4e5f6...
```

If the developer is using ISF-Core's `compose.yml`, the key is automatically mapped:

```yaml
# compose.yml (isf-dev container)
environment:
  - AI_PROXY_VIRTUAL_KEY=${AI_PROXY_VIRTUAL_KEY}
```

The `isf-core` backend reads this variable and injects it as an `Authorization: Bearer <key>` header on every LLM request to `ai-proxy`. No frontend UI changes needed.

---

## Step 5: Verify Spend Logging

Make a test request through the proxy (any normal chat message works). Then export the spend logs:

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py export-csv --month 2025-01
```

**Output:**

```
📊 Exported 42 records to spend_report_2025-01.csv
```

Open the CSV file to review:

| Column | Description |
| :--- | :--- |
| `user_id` | Developer username (e.g., `dev_john`) |
| `project` | Project name (e.g., `project_alpha`) |
| `model` | LLM model used (e.g., `gpt-4o`, `gemini-2.5-pro`) |
| `token_in` | Total prompt tokens sent to the model |
| `token_out` | Total completion tokens generated |
| `cache_hit` | Prompt tokens served from cache (cheaper) |
| `cache_miss` | Prompt tokens processed fresh (full price) |
| `cost_usd` | Calculated cost based on `models.yaml` pricing |
| `timestamp` | When the request completed (UTC) |

---

## 🛠️ Admin CLI Reference

All commands run inside the `ai-proxy` container:

### Generate a New Key

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py generate <user> --project <project>
```

### Revoke (Deactivate) a Key

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py revoke <user> --project <project>
```

This sets the key's status to `inactive` in `data/virtual_key_admin.yml`. The key is **not deleted** — audit trail preserved. The developer will receive a `401 Unauthorized` on their next request.

### List All Users & Keys

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py list
```

### Export Spend to CSV

```bash
# Current month
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py export-csv

# Specific month
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py export-csv --month 2025-01

# Custom output file
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py export-csv --month 2025-01 --output my_report.csv
```

### Reload Key Index (after manual YAML edits)

```bash
docker compose exec ai-proxy python ai_proxy/virtual_key_admin.py reimport
```

---

## 🗄️ Database Architecture

```
┌───────────────────────────────────────────────────┐
│               DATA STORAGE LAYER                  │
├───────────────────────────────────────────────────┤
│                                                   │
│  DATABASE_URL set?                                │
│       │                                           │
│       ├── YES (postgresql://...) ──► Supabase/PostgreSQL
│       │                                   (production, team use)
│       │                                           │
│       └── NO ──► SQLite fallback                  │
│                   data/proxy_usage.db             │
│                   (zero-config, auto-created)     │
│                                                   │
├───────────────────────────────────────────────────┤
│  KEY STORAGE (always YAML)                        │
│  data/virtual_key_admin.yml                       │
│  (loaded into memory at startup)                  │
└───────────────────────────────────────────────────┘
```

Both files persist on your host filesystem via the `./data:/app/data` Docker volume mount — they survive `docker compose down` and container rebuilds.

### Setting up Supabase (PostgreSQL)

If you are running in a team environment or expecting high concurrency, it is highly recommended to switch from SQLite to Supabase (PostgreSQL). 

1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Get your connection string from **Project Settings > Database > Connection string > URI**.
3. Open your `.env` file and add the `DATABASE_URL` variable. Make sure it starts with `postgresql://` (or `postgres://`).

**Example `.env` configuration:**

```bash
# Enable the virtual key system
ENABLE_VIRTUAL_KEY=true

# Provide the Supabase PostgreSQL connection string
# Replace [YOUR-PASSWORD], [YOUR-HOST], and [YOUR-PORT] with your actual Supabase credentials
DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:[YOUR-PORT]/postgres"
```

When you restart the `ai-proxy` container, it will automatically connect to Supabase, create the `spend_logs` table if it doesn't exist, and seamlessly transition from SQLite.

---

## 🔐 Security Notes

- **Keys are hashed** (SHA-256) before storage in the database. The raw `sk-virt-xxx` key only exists in the YAML file.
- **YAML file permissions:** Keep `data/virtual_key_admin.yml` restricted (chmod 600).
- **`data/` is git-ignored** by default. Never commit your virtual key YAML or SQLite DB to version control.
- **Revoked keys** remain in the YAML for audit purposes (`status: inactive`) but are rejected by the proxy.

---

## ❓ Troubleshooting

| Problem | Solution |
| :--- | :--- |
| **"Failed to load virtual key index"** | Your `data/virtual_key_admin.yml` may be empty or malformed. Generate a key first, or check the YAML syntax. |
| **401 Unauthorized on requests** | Verify the key is `active` in the YAML. Run `list` to check status. Ensure the developer's `.env` has the correct `AI_PROXY_VIRTUAL_KEY`. |
| **`cost_usd` always 0.0** | The model may be missing pricing in `models.yaml`. Add `cost_input_per_1m` and `cost_output_per_1m` to the model's config. |
| **SQLite database locked** | Only one process should write to the DB. Avoid running `export-csv` while streaming large requests. |

---

## 📚 Related Documentation

- **[ai-proxy Virtual Key Architecture](../../docs/ai_proxy_virtual_key_architecture.md)** — Full technical architecture
- **[README: Why AI-Proxy Is Separate](../../README.md#-why-ai-proxy-is-separate-from-isf-core)** — Security rationale
- **[Option 1: Supabase Migration](option1_supabase.md)** — Upgrade to PostgreSQL for team use
- **[Option 9: Mnemon Memory](option9_mnemon_memory.md)** — Cross-session AI memory

---

**Next:** After setting up virtual keys, consider **[Option 1: Supabase Migration](option1_supabase.md)** if you outgrow the local SQLite database.
