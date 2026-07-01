import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

# Ensure the project root is on sys.path so backend.* imports work
import os as _os
_project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.core.chat_storage.chat_storage import ChatStorage  # noqa: E402
from backend.server.state import global_state  # noqa: E402

logger = logging.getLogger(__name__)


def _find_and_remove_background_job(active_jobs: Any) -> str:
    """Finds the background job matching 'token' or 'housekeeping' and removes it."""
    job_name = "Token Usage Housekeeping"
    found_job = None
    for name in active_jobs:
        if "token" in name.lower() or "housekeeping" in name.lower():
            found_job = name
            break

    if found_job:
        job_name = found_job
        try:
            active_jobs.remove(found_job)
        except KeyError:
            pass
    return job_name


def _log_scheduler_execution(
    scheduler: Any,
    log_id: Any,
    success: bool,
    duration_ms: int,
    error_message: str | None
) -> None:
    """Safely parses log_id and logs the execution end for the scheduler."""
    parsed_log_id = None
    if isinstance(log_id, int):
        parsed_log_id = log_id
    elif isinstance(log_id, str) and log_id.isdigit():
        parsed_log_id = int(log_id)

    if parsed_log_id is not None:
        if success:
            scheduler._log_execution_end(
                parsed_log_id,
                "SUCCESS",
                duration_ms,
                response_payload={"message": "Token Usage Housekeeping completed successfully."}
            )
        else:
            scheduler._log_execution_end(
                parsed_log_id,
                "FAILED",
                duration_ms,
                response_payload={"message": f"Token Usage Housekeeping failed: {error_message}"}
            )


def run_token_housekeeping_workflow(log_id: str) -> None:
    """Executes the housekeeping logic for token usage older than 1 hour."""
    start_time = time.time()
    logger.info(f"[{log_id}] Starting Token Usage Housekeeping...")
    success = False
    error_message: str | None = None
    try:
        storage = ChatStorage()

        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=1)
        cutoff_str = cutoff_date.isoformat().replace('+00:00', 'Z')

        if storage.use_supabase and storage.supabase:
            _run_supabase_housekeeping(storage, cutoff_str, log_id)
        else:
            _run_sqlite_housekeeping(storage, cutoff_str, log_id)
        success = True
    except Exception as e:
        error_message = str(e)
        logger.error(f"[{log_id}] Token Usage Housekeeping failed: {e}")
    finally:
        # Scheduler Cleanup logic
        duration_ms = int((time.time() - start_time) * 1000)
        active_jobs = getattr(global_state, "active_background_jobs", set())

        job_name = _find_and_remove_background_job(active_jobs)

        logger.info(f"[{log_id}] Cleaning up active background job '{job_name}' and setting status to Idle.")
        scheduler = getattr(global_state, "scheduler", None)
        if scheduler:
            scheduler._update_task_state(job_name, "Idle")
            _log_scheduler_execution(scheduler, log_id, success, duration_ms, error_message)


def _run_sqlite_housekeeping(storage: ChatStorage, cutoff_str: str, log_id: str) -> None:
    try:
        with storage._get_conn() as conn:
            # 1. Select old rows
            cursor = conn.execute("""
                SELECT strftime('%Y-%m-%d %H:00', timestamp) as hour_bucket,
                       model, SUM(token_in) as token_in, SUM(token_out) as token_out,
                       SUM(cost) as cost, COUNT(*) as request_count,
                       SUM(cache_hit) as cache_hit, SUM(cache_miss) as cache_miss
                FROM token_usage
                WHERE timestamp < ?
                GROUP BY hour_bucket, model
            """, (cutoff_str,))

            rows = cursor.fetchall()
            if not rows:
                logger.info(f"[{log_id}] No SQLite records older than 1 hour to aggregate.")
                return

            # 2. Upsert into token_usage_hourly
            conn.executemany("""
                INSERT INTO token_usage_hourly (hour_bucket, model, token_in, token_out, cost, request_count, cache_hit, cache_miss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(hour_bucket, model) DO UPDATE SET
                    token_in = token_usage_hourly.token_in + excluded.token_in,
                    token_out = token_usage_hourly.token_out + excluded.token_out,
                    cost = token_usage_hourly.cost + excluded.cost,
                    request_count = token_usage_hourly.request_count + excluded.request_count,
                    cache_hit = token_usage_hourly.cache_hit + excluded.cache_hit,
                    cache_miss = token_usage_hourly.cache_miss + excluded.cache_miss
            """, rows)

            # 3. Delete old rows
            cursor = conn.execute("DELETE FROM token_usage WHERE timestamp < ?", (cutoff_str,))
            logger.info(f"[{log_id}] SQLite housekeeping complete: aggregated {len(rows)} hour-model buckets, deleted {cursor.rowcount} old raw records.")
    except Exception as e:
        logger.error(f"[{log_id}] SQLite housekeeping failed: {e}")


def _fetch_supabase_old_rows(storage: ChatStorage, cutoff_str: str) -> List[Dict[str, Any]]:
    """Fetches old token usage rows from Supabase in chunks."""
    all_old_rows: List[Dict[str, Any]] = []
    limit = 1000
    offset = 0
    if storage.supabase is None:
        return all_old_rows
    while True:
        resp = storage.supabase.table("token_usage").select("*").lt("timestamp", cutoff_str).range(offset, offset + limit - 1).execute()
        if not resp.data:
            break
        all_old_rows.extend(resp.data)
        if len(resp.data) < limit:
            break
        offset += limit
    return all_old_rows


def _aggregate_rows_in_memory(all_old_rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[Any]]:
    """Aggregates raw rows into hourly-model buckets and extracts list of IDs to delete."""
    aggregated: Dict[str, Dict[str, Any]] = {}
    ids_to_delete: List[Any] = []
    for row in all_old_rows:
        row_id = row.get("id")
        if row_id is not None:
            ids_to_delete.append(row_id)
        ts = row.get("timestamp")
        if not ts:
            continue

        try:
            hour_bucket = str(ts)[:13] + ":00"
        except Exception:
            continue

        model = str(row.get("model", "unknown"))
        key = f"{hour_bucket}::{model}"

        if key not in aggregated:
            aggregated[key] = {
                "hour_bucket": hour_bucket,
                "model": model,
                "token_in": 0,
                "token_out": 0,
                "cost": 0.0,
                "request_count": 0,
                "cache_hit": 0,
                "cache_miss": 0
            }

        aggregated[key]["token_in"] += int(row.get("token_in") or 0)
        aggregated[key]["token_out"] += int(row.get("token_out") or 0)
        aggregated[key]["cost"] += float(row.get("cost") or 0.0)
        aggregated[key]["request_count"] += 1
        aggregated[key]["cache_hit"] += int(row.get("cache_hit") or 0)
        aggregated[key]["cache_miss"] += int(row.get("cache_miss") or 0)
    return aggregated, ids_to_delete


def _delete_supabase_rows_in_chunks(storage: ChatStorage, ids_to_delete: List[Any]) -> int:
    """Deletes list of IDs from Supabase table in chunks of 500."""
    if storage.supabase is None:
        return 0
    chunk_size = 500
    deleted_count = 0
    for i in range(0, len(ids_to_delete), chunk_size):
        chunk = ids_to_delete[i:i+chunk_size]
        storage.supabase.table("token_usage").delete().in_("id", chunk).execute()
        deleted_count += len(chunk)
    return deleted_count


def _run_supabase_housekeeping(storage: ChatStorage, cutoff_str: str, log_id: str) -> None:
    try:
        if storage.supabase is None:
            logger.info(f"[{log_id}] Supabase client is not available.")
            return

        # 1. Fetch old rows in chunks
        all_old_rows = _fetch_supabase_old_rows(storage, cutoff_str)

        if not all_old_rows:
            logger.info(f"[{log_id}] No Supabase records older than 1 hour to aggregate.")
            return

        # 2. Aggregate in memory
        aggregated, ids_to_delete = _aggregate_rows_in_memory(all_old_rows)

        upsert_payload = list(aggregated.values())

        # 3. Upsert to token_usage_hourly
        try:
            storage.supabase.table("token_usage_hourly").upsert(upsert_payload, on_conflict="hour_bucket,model").execute()
        except Exception as upsert_err:
            logger.error(f"[{log_id}] Supabase token_usage_hourly UPSERT failed. Ensure 'token_usage_hourly' table exists with unique constraint on (hour_bucket, model). Error: {upsert_err}")
            return

        # 4. Delete old rows in chunks
        deleted_count = _delete_supabase_rows_in_chunks(storage, ids_to_delete)

        logger.info(f"[{log_id}] Supabase housekeeping complete: aggregated {len(aggregated)} hour-model buckets, deleted {deleted_count} old raw records.")
    except Exception as e:
        logger.error(f"[{log_id}] Supabase housekeeping failed: {e}")


if __name__ == "__main__":
    import uuid
    # Standard entry point when invoked via ISOLATED_PROCESS
    run_token_housekeeping_workflow(str(uuid.uuid4()))
