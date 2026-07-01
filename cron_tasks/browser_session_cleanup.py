"""
Standalone cron script: browser session cleanup.

Called by the Cron_Daemon scheduler as an ISOLATED_PROCESS.
Iterates over all browser sessions, auto-closing orphaned running sessions
(marked completed if ≥4 steps, physically deleted otherwise).

No HTTP round-trip required — runs directly via subprocess.
"""
import logging
import os
import sys

# Ensure the project root is on sys.path so backend.* imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("browser_session_cleanup")

from backend.browser.session_logger import get_all_sessions  # noqa: E402


def main() -> None:
    logger.info("Starting browser session orphan cleanup...")
    sessions = get_all_sessions(summary_only=True)
    logger.info(
        "Orphan cleanup completed. %d session(s) examined.",
        len(sessions),
    )
    # Emit structured result for the scheduler to parse
    print(
        "__CRON_RESULT__ "
        '{"status": "SUCCESS", "response_payload": '
        '{"message": "Orphan cleanup completed", "sessions_examined": %d}}'
        % len(sessions)
    )


if __name__ == "__main__":
    main()
