import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PresetSQLiteSeed")

# Determine paths relative to this script
BASE_DIR: Path = Path(__file__).resolve().parent
DB_PATH: Path = BASE_DIR / "data" / "chat_history.db"
SQL_PATH: Path = BASE_DIR / "sqlite_seed_data.sql"

def run_seed() -> None:
    """Read sqlite_seed_data.sql and execute it inside the SQLite database."""
    if not SQL_PATH.exists():
        logger.error(f"SQL seed file not found: {SQL_PATH}")
        return

    # Ensure parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Connecting to database: {DB_PATH}")
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        logger.info(f"Reading SQL seed file: {SQL_PATH}")
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            sql_content: str = f.read()

        logger.info("Executing seed script...")
        cursor.executescript(sql_content)
        conn.commit()
        conn.close()
        logger.info("✅ Database seeded successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to seed database: {e}")

if __name__ == "__main__":
    run_seed()
