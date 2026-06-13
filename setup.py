import sys
import json
import shutil
import sqlite3
import secrets
import subprocess
from pathlib import Path

def ensure_key_in_env(env_path: Path, key: str, value: str = "") -> None:
    """Ensure a key=value line exists in an .env file. Appends if missing."""
    with open(env_path, "r") as f:
        content = f.read()
    if f"\n{key}=" in content or content.startswith(f"{key}="):
        return
    with open(env_path, "a") as f:
        f.write(f"\n{key}={value}\n")
    print(f"   ➕ Added {key} to .env")

def setup_env():
    print("\n" + "="*50)
    print("🚀 ISF-Core Initial Setup")
    print("="*50)

    env_path = Path(".env")
    env_ai_proxy_path = Path(".env.ai_proxy.example")
    sample_env = Path(".env.sample")
    supabase_sample = Path("supabase-docker/.env.sample")

    if not env_path.exists():
        # Priority: local .env.sample > supabase-docker/.env.sample > fallback
        if sample_env.exists():
            shutil.copy(sample_env, env_path)
            print("✅ Created .env from local template.")
        elif supabase_sample.exists():
            shutil.copy(supabase_sample, env_path)
            print("✅ Created .env from supabase-docker template.")
        else:
            with open(env_path, "w") as f:
                f.write("TAVILY_API_KEY=\n")
            print("✅ Created new .env file.")

        # Generate a random secret key for the backend
        secret_key = secrets.token_hex(32)
        with open(env_path, "a") as f:
            f.write(f"\nISF_SECRET_KEY={secret_key}\n")
    else:
        print("✅ .env file already exists.")

    # Always ensure critical keys exist (even in pre-existing .env)
    ensure_key_in_env(env_path, "TAVILY_API_KEY")
    ensure_key_in_env(env_path, "ISF_SECRET_KEY", secrets.token_hex(32))

    # --- .env.ai_proxy.example (separate API keys template for ai-proxy service) ---
    if not env_ai_proxy_path.exists():
        with open(env_ai_proxy_path, "w") as f:
            f.write("""# ============================================================
# .env.ai_proxy.example — API keys for the AI Proxy service
# ============================================================
# Copy this file to .env.ai_proxy and fill in the keys for the
# LLM providers you wish to use. You only need to configure
# the providers you actually use.
# ============================================================

GOOGLE_API_KEY=
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
""")
        print("✅ Created .env.ai_proxy.example template file.")

        print("\n⚠️  ACTION REQUIRED: Configure your API Keys ⚠️")
        print("-" * 50)
        print("To power the AI Proxy, you must provide your LLM API keys.")
        print("Please copy '.env.ai_proxy.example' to '.env.ai_proxy' and fill in at least one of:")
        print("")
        print("  🔑 GOOGLE_API_KEY    (Required for Gemini multimodal models)")
        print("      👉 Get it here: https://aistudio.google.com/app/apikey")
        print("  🔑 DEEPSEEK_API_KEY  (Required for DeepSeek reasoning models)")
        print("      👉 Get it here: https://platform.deepseek.com/api_keys")
        print("  🔑 OPENAI_API_KEY    (Optional, for GPT-4o models)")
        print("      👉 Get it here: https://platform.openai.com/api-keys")
        print("")
        print("  📝 TAVILY_API_KEY    (Required for web search — goes in .env)")
        print("      👉 Get it here: https://app.tavily.com/home")
        print("-" * 50)
    else:
        print("✅ .env.ai_proxy.example template file already exists. Skipping creation.")

def setup_sqlite():
    print("\n📦 Initializing Local SQLite Database...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    db_path = data_dir / "chat_history.db"

    # Connect to SQLite (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the cron_scheduled_jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cron_scheduled_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            cron_expression TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            target_type TEXT NOT NULL,
            job_type TEXT NOT NULL,
            target_payload TEXT DEFAULT '{}',
            target_payload_json TEXT DEFAULT '{}',
            is_deleted BOOLEAN DEFAULT 0,
            last_run_at TIMESTAMP,
            next_run_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create the browser_credentials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS browser_credentials (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            environment TEXT DEFAULT 'production',
            username TEXT NOT NULL,
            password_encrypted TEXT NOT NULL,
            input_schema TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database ready.")

def setup_skip_config() -> None:
    print("\n⚙️ Configuring Services Skip Config...")
    backend_dir = Path("backend")
    backend_dir.mkdir(exist_ok=True)
    skip_config_path = backend_dir / ".skip_config.json"
    
    skip_config_data = {
        "core_skip": ["mnemon", "sonarqube", "supabase_db_agent", "supabase", "telegram_bot"],
        "mcp_skip": ["gateway", "playwright", "janus_pro", "vector_graph_rag"]
    }
    
    with open(skip_config_path, "w") as f:
        json.dump(skip_config_data, f, indent=2)
    print("✅ Created backend/.skip_config.json with default skipped services.")

if __name__ == "__main__":
    setup_env()
    setup_sqlite()
    setup_skip_config()

    # Automatically preset seed data if the script is available
    preset_script = Path("preset_sqlite_seed_data.py")
    if preset_script.exists():
        try:
            print("\n🌱 Running preset_sqlite_seed_data.py to sync seed data...")
            subprocess.run([sys.executable, str(preset_script)], check=True)
        except Exception as e:
            print(f"⚠️ Error running preset seed script: {e}")

    print("\n" + "="*50)
    print("🎉 Setup Complete!")
    print("You are now ready to start the application.")
    print("")
    print("🚀 Start ISF-Core + AI-Proxy together (recommended):")
    print("   python start_isf_core.py")
    print("")
    print("🔧 Or start the AI-Proxy standalone:")
    print("   docker compose -f ai-proxy.yml up -d")
    print("")
    print("🛑 To shut down later:")
    print("   python shutdown_isf_core.py")
    print("")
    print("📝 Don't forget to copy .env.ai_proxy.example to .env.ai_proxy and configure your API keys!")
    print("="*50 + "\n")