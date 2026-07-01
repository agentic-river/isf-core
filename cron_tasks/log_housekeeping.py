"""
Standalone cron script: log housekeeping.

Called by the Cron_Daemon scheduler as an ISOLATED_PROCESS.
Prunes system_logs older than 3 days from:
  1. Supabase (if available) — the primary data store
  2. Local SQLite (fallback when Supabase is not configured)
  3. Local log file (ai_developer.log + rotated *.log.* artefacts)

No HTTP round-trip required — runs directly via subprocess.
"""
import logging
import os
import sys
import glob
import re
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# Ensure the project root is on sys.path so backend.* imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("log_housekeeping")


def _get_supabase_client() -> Optional[Any]:
    """Try to get a Supabase client, returning None if unavailable."""
    try:
        from backend.core.supabase_client import SupabaseManager
        return SupabaseManager.get_client_from_env()
    except Exception:
        return None


def _prune_supabase_system_logs(cutoff_iso: str) -> int:
    """Delete rows from public.system_logs older than the cutoff. Returns deleted count."""
    supabase = _get_supabase_client()
    if not supabase:
        logger.info("Supabase not available — skipping DB pruning.")
        return -1  # sentinel: unavailable

    try:
        res = supabase.table("system_logs").delete().lt("timestamp", cutoff_iso).execute()
        deleted = len(res.data) if res.data else 0
        logger.info("Supabase DB pruning complete. Trimmed %d log(s) older than %s.", deleted, cutoff_iso)
        return deleted
    except Exception as exc:
        logger.error("Supabase DB pruning failed: %s", exc)
        raise


def _prune_sqlite_system_logs(cutoff_iso: str) -> int:
    """Delete rows from the local SQLite system_logs table older than the cutoff."""
    try:
        from backend.server.constants import SQLITE_DB_PATH
        import sqlite3
    except ImportError:
        logger.info("SQLite not available — skipping local DB pruning.")
        return -1

    if not os.path.exists(SQLITE_DB_PATH):
        logger.info("SQLite DB file not found at %s — skipping local DB pruning.", SQLITE_DB_PATH)
        return 0

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        cursor = conn.execute(
            "DELETE FROM system_logs WHERE timestamp < ?",
            (cutoff_iso,),
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info("SQLite DB pruning complete. Trimmed %d log(s) older than %s.", deleted, cutoff_iso)
        return deleted
    except Exception as exc:
        # The table may not exist if the SQLite schema didn't create it
        if "no such table" in str(exc).lower():
            logger.info("No system_logs table in SQLite — skipping local DB pruning.")
            return 0
        logger.error("SQLite DB pruning failed: %s", exc)
        raise


def _delete_rotated_logs(log_file_path: str) -> int:
    """Delete rotated log files matching *.log.* (e.g. ai_developer.log.1)."""
    renamed_logs = glob.glob(f"{log_file_path}.*")
    deleted = 0
    for rlog in renamed_logs:
        try:
            os.remove(rlog)
            logger.info("Deleted rotated log file: %s", rlog)
            deleted += 1
        except Exception as exc:
            logger.error("Failed to delete %s: %s", rlog, exc)
    return deleted


def _filter_log_file_lines(log_file_path: str, cutoff_date: datetime) -> int:
    """Keep only log lines whose timestamp is >= cutoff_date. Returns lines removed."""
    if not os.path.exists(log_file_path):
        return 0

    date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
    with open(log_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    kept_lines: list[str] = []
    current_block_keep = True
    for line in lines:
        match = date_pattern.search(line)
        if match:
            try:
                log_date = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                current_block_keep = log_date >= cutoff_date
            except ValueError:
                pass
        if current_block_keep:
            kept_lines.append(line)

    with open(log_file_path, "w", encoding="utf-8") as f:
        f.writelines(kept_lines)

    removed = len(lines) - len(kept_lines)
    return removed


def _trim_local_log_file(cutoff_date: datetime) -> Dict[str, int]:
    """Trim rotated log files and old lines from the main log file."""
    from backend.core.engine import get_app_settings
    settings = get_app_settings()
    log_file_path = settings.log_file

    rotated_deleted = _delete_rotated_logs(log_file_path)
    lines_removed = _filter_log_file_lines(log_file_path, cutoff_date)

    logger.info(
        "Local log file pruning complete. Deleted %d rotated artefact(s), removed %d old line(s) from %s.",
        rotated_deleted, lines_removed, log_file_path,
    )
    return {"rotated_files_deleted": rotated_deleted, "log_lines_removed": lines_removed}


def main() -> None:
    start_time = time.time()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=3)
    cutoff_iso = cutoff_date.isoformat()

    result: Dict[str, Any] = {"status": "SUCCESS"}
    error_message: Optional[str] = None

    logger.info("Starting log housekeeping (cutoff: %s)...", cutoff_iso)

    # 1. Prune Supabase DB logs (primary)
    db_deleted = -1
    try:
        db_deleted = _prune_supabase_system_logs(cutoff_iso)
    except Exception as exc:
        logger.error("Supabase pruning failed, will try SQLite fallback: %s", exc)
        result["status"] = "PARTIAL"
        error_message = str(exc)

    # 2. Prune SQLite DB logs (fallback or complementary)
    sqlite_deleted = -1
    try:
        sqlite_deleted = _prune_sqlite_system_logs(cutoff_iso)
    except Exception as exc:
        logger.error("SQLite pruning failed: %s", exc)
        if result["status"] == "SUCCESS" and db_deleted < 0:
            result["status"] = "FAILED"
            error_message = str(exc)

    # 3. Trim local log files (always runs)
    file_stats: Dict[str, int] = {}
    try:
        file_stats = _trim_local_log_file(cutoff_date)
    except Exception as exc:
        logger.error("Local file trimming failed: %s", exc)
        if result["status"] != "FAILED":
            result["status"] = "PARTIAL"
        error_message = error_message or str(exc)

    duration_ms = int((time.time() - start_time) * 1000)

    response_payload: Dict[str, Any] = {
        "message": "Log housekeeping completed",
        "db_deleted": db_deleted if db_deleted >= 0 else 0,
        "sqlite_deleted": sqlite_deleted if sqlite_deleted >= 0 else 0,
        "rotated_files_deleted": file_stats.get("rotated_files_deleted", 0),
        "log_lines_removed": file_stats.get("log_lines_removed", 0),
    }

    # Emit structured result for the scheduler to parse
    cr_payload: Dict[str, Any] = {
        "status": result["status"],
        "response_payload": response_payload,
        "duration_ms": duration_ms,
    }
    if error_message:
        cr_payload["error_message"] = error_message

    print(f"__CRON_RESULT__ {json.dumps(cr_payload)}")


if __name__ == "__main__":
    main()
