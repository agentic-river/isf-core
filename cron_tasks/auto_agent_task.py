import asyncio
import logging
import os
import sys
import time
from typing import Optional

# Ensure the project root is on sys.path so backend.* imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.server.state import global_state  # noqa: E402
from backend.core.chat_storage import ChatStorage  # noqa: E402
from backend.core.chat_helpers import _prepare_genai_history  # noqa: E402
from backend.core.engine import EventBus  # noqa: E402
from backend.server.websocket_manager import broadcast_message_to_websockets_sync  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto_agent_task")

AUTO_AGENT_TASK_NAME = "Auto Agent Task"

async def run_auto_agent_workflow(log_id: Optional[int] = None):
    start_time = time.time()
    try:
        db = ChatStorage()
        sessions = db.get_sessions(limit=1, tag_contains="?")

        if not sessions:
            logger.info("No chat sessions flagged with '?' found. Stopping workflow.")
            return

        target_session = sessions[0]
        session_id = target_session['id']
        tags = target_session.get('tags', [])
        
        # Determine Mode
        is_execute = any('!' in str(t) for t in tags)
        mode_str = "Execute Mode" if is_execute else "Plan Mode"
        logger.info(f"Picked session {session_id} for background work. Running in {mode_str}.")

        # Retrieve Context
        from backend.routers.chat import MessageInput
        messages = db.get_messages(session_id)
        history_msgs = [
            MessageInput(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                images=msg.get("images", []) or []
            )
            for msg in messages
        ]
        genai_history = _prepare_genai_history(history_msgs)

        # Instantiate Autonomous Agent Session
        chat = global_state.client.create(
            model_role="auto_agent",
            system_instruction="You are an autonomous background process resuming the user's previous request.",
            history=genai_history,
            tools=global_state.tools,
            dry_run=not is_execute
        )

        prompt = "Please continue where we left off and fulfill the requested task based on the chat history."
        response = await asyncio.to_thread(chat.send_message, prompt)

        # Update and Save Messages
        new_user_msg = {"role": "user", "content": "[System] Autonomous task initiated.", "images": []}
        new_model_msg = {"role": "ai", "content": response.text or "Task completed.", "images": []}

        messages.extend([new_user_msg, new_model_msg])

        target_run_mode = "E" if is_execute else "P"
        logger.info(f"Saving session {session_id} with last_run_mode={target_run_mode} and status=unread")
        db.save_session(
            session_id=session_id,
            title=target_session.get("title", AUTO_AGENT_TASK_NAME),
            messages=messages,
            last_run_mode=target_run_mode,
            status="unread"
        )

        # Clean tags
        new_tags = [t.replace('?', '').replace('!', '').strip() for t in tags]
        new_tags = [t for t in new_tags if t]  # Remove empty tags
        
        logger.info(f"Updating session metadata for {session_id} with cleaned tags: {new_tags}")
        db.update_session_metadata(session_id, tags=new_tags)

        # Broadcast chat_update and job_completed to frontend via WebSockets instantly
        chat_update_payload = {
            "chat_update": {
                "sessionId": session_id,
                "title": target_session.get("title", AUTO_AGENT_TASK_NAME),
                "messages": messages,
                "status": "unread",
                "last_run_mode": target_run_mode
            }
        }
        logger.info(f"Broadcasting chat_update to websockets: {chat_update_payload}")
        broadcast_message_to_websockets_sync(chat_update_payload)

        job_completed_payload = {
            "job_completed": {
                "task": AUTO_AGENT_TASK_NAME,
                "payload": f'{{"session_id": "{session_id}"}}'
            }
        }
        logger.info(f"Broadcasting job_completed to websockets: {job_completed_payload}")
        broadcast_message_to_websockets_sync(job_completed_payload)

        # Broadcast global event for frontend bell notification
        EventBus.broadcast_event("job_completed", AUTO_AGENT_TASK_NAME, {"session_id": session_id})
        
        logger.info(f"Successfully processed session {session_id} and cleaned tags.")

    except Exception as e:
        logger.error(f"Auto agent task failed: {e}")
    finally:
        # Scheduler Cleanup logic
        duration_ms = int((time.time() - start_time) * 1000)
        scheduler = getattr(global_state, "scheduler", None)
        if scheduler:
            scheduler._update_task_state(AUTO_AGENT_TASK_NAME, "Idle")
            if log_id is not None:
                scheduler._log_execution_end(
                    log_id,
                    "SUCCESS",
                    duration_ms,
                    response_payload={"message": "Auto Agent completed successfully."}
                )

if __name__ == "__main__":
    # Standard entry point when invoked via ISOLATED_PROCESS
    asyncio.run(run_auto_agent_workflow())