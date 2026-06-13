# backend/tasks/sample_task.py
import logging
from typing import Dict, Any

logger = logging.getLogger("job_scheduler")

def run(scheduler: Any, payload: Dict[str, Any]) -> None:
    """
    Sample Dynamic Task designed to be executed dynamically by APScheduler.
    
    Args:
        scheduler: The running JobScheduler instance, giving access to self.settings and self._get_supabase()
        payload: Dict containing custom arguments passed from the cron_scheduled_jobs.target_payload
    """
    logger.info("=========================================")
    logger.info("🚀 Starting Dynamic Task execution!")
    
    # 1. Retrieve arguments from the target_payload
    recipient = payload.get("recipient", "System Administrator")
    message = payload.get("message", "Custom background execution completed.")
    
    logger.info(f"Recipient: {recipient}")
    logger.info(f"Custom Message: {message}")
    
    # 2. Perform a sample operation using the dynamic scheduler's DB connections
    try:
        supabase = scheduler._get_supabase()
        if supabase:
            # We can perform logs, inserts, or queries natively!
            logger.info("Supabase client is connected and active within dynamic task.")
    except Exception as e:
        logger.error(f"Failed to access database connection: {e}")
        
    logger.info("🎉 Dynamic Task finished successfully!")
    logger.info("=========================================")
