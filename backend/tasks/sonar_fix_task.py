import asyncio
import glob
import logging
import os
import time
from typing import Optional
from backend.core.sonar_tools import SonarQubeTools
from backend.core.devops_tools import DevOpsTools
from backend.server.state import global_state

logger = logging.getLogger("sonar_fix_task")

async def invoke_ai_agent(prompt: str, role: str) -> str:
    """Wrapper to invoke the agent autonomously for cron execution."""
    global_state.settings.reload_models_config()
    logger.info(f"Invoking Autonomous AI Agent with role: {role}")
    full_prompt = f"Role: {role}\n\n{prompt}" if role else prompt

    # Instantiate the same ReAct Chat Session used by the Chat UI
    chat = global_state.client.create(
        model_role=role,
        system_instruction="You are an autonomous background process.",
        tools=global_state.tools,
        dry_run=False
    )

    try:
        # Run the full agent loop (allows recursive smart_replace tool usage)
        response = await asyncio.to_thread(chat.send_message, full_prompt)
        return response.text or ""
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return f"Error: {e}"

def _get_files_with_issues(sonar_tools: SonarQubeTools) -> list[str]:
    """Fetch files with issues from SonarQube (up to 10 unique files)."""
    issues_res = sonar_tools.get_sonar_issues_by_severity("INFO,MINOR,MAJOR,CRITICAL,BLOCKER")
    if not issues_res or isinstance(issues_res, str):
        return []

    unique_files = []
    for issue in issues_res:
        file_path = issue.get("file") or issue.get("component")
        if file_path:
            if ":" in file_path:
                file_path = file_path.split(":", 1)[1]
            if file_path not in unique_files:
                unique_files.append(file_path)
        if len(unique_files) == 10:
            break
    return unique_files



def _check_pyright_ruff_errors(err_lower: str) -> bool:
    """Helper to parse Pyright and Ruff issues from syntax check outputs."""
    if "pyright analysis:" in err_lower:
        import re
        m = re.search(r'(\d{1,6})\s+error', err_lower)  # NOSONAR
        if m and int(m.group(1)) > 0:
            return True
    if "ruff analysis:" in err_lower and "ruff analysis: ok" not in err_lower:
        if "error" in err_lower or "failed" in err_lower:
            return True
    return False

def _has_syntax_or_analysis_errors(syntax_errors: Optional[str]) -> bool:
    """Check if the syntax_errors report contains any actual errors."""
    if not syntax_errors:
        return False

    err_lower = syntax_errors.lower()
    if "syntax check skipped" in err_lower:
        return False

    if "syntax ok" in err_lower or "success: syntax is perfect" in err_lower:
        return _check_pyright_ruff_errors(err_lower)

    return "syntax error" in err_lower or "failed" in err_lower or "error:" in err_lower

async def _check_and_fix_syntax(devops: DevOpsTools, target_file: str):
    """Run check syntax and invoke AI to fix any syntax/pyright errors."""
    logger.info("Step 6: Running syntax check.")
    syntax_errors = await asyncio.to_thread(devops.check_syntax, target_file)

    if _has_syntax_or_analysis_errors(syntax_errors):
        logger.info(f"Syntax/Pyright errors found in {target_file}. Invoking AI to fix them.")
        fix_prompt = (
            f"Run check syntax and fix the following Pyright/Syntax issues in {target_file}:\n{syntax_errors}\n\n"
            "After fixing, remove any temporary files, debug scripts, or intermediate artifacts you created. "
            "If {target_file} is a test file, then don't need to fix pyright issues. "
            "The workspace must be left clean."
        )
        await invoke_ai_agent(prompt=fix_prompt, role="sonar_fixer")

async def _cleanup_workspace():
    """Remove temporary working files created during the AI fixing session."""
    import tempfile
    tmp_dir = tempfile.gettempdir()
    temp_patterns = [
        os.path.join(tmp_dir, "sonar_*.py"),
        os.path.join(tmp_dir, "test_*.py"),
        os.path.join(tmp_dir, "debug_*.py"),
        "backend/data/tmp/*.py",
    ]

    for pattern in temp_patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                logger.info(f"Cleaned up temp file: {f}")
            except OSError:
                pass

    # Also ask AI to clean up any files it knows it created
    await invoke_ai_agent(
        prompt=(
            "Clean up any temporary working files, test scripts, debug logs, "
            "or intermediate artifacts you created during this session. "
            "Use execute_shell_command to remove them. "
            "Do NOT delete any production code, config files, or persistent data."
        ),
        role="sonar_fixer"
    )

def _select_unprocessed_file(unique_files: list[str], processed_files: set[str]) -> Optional[str]:
    """Helper to select one file that has not been processed yet."""
    for f in unique_files:
        if f not in processed_files:
            return f
    return None

async def _invoke_fix_agent(target_file: str):
    """Helper to invoke AI agent to fix Sonar issues for a target file."""
    logger.info("Step 4: Invoking AI to fix Sonar issues.")
    prompt = (
        f"Use @rules/Sonar_Issue_Fixing_Protocol.md to fix all sonar issues found in {target_file}. "
        "After fixing, remove any temporary files, debug scripts, or intermediate artifacts you created. "
        "The workspace must be left clean."
    )
    await invoke_ai_agent(prompt=prompt, role="sonar_fixer")

async def _process_sonar_fix_loops(sonar_tools: SonarQubeTools, devops: DevOpsTools):
    """Helper to process Sonar fix loops, keeping complexity low."""
    max_loops = 10
    loops_run = 0
    processed_files = set()  # Track files already handled in this cron invocation

    while loops_run < max_loops:
        logger.info(f"Starting Sonar fix loop {loops_run + 1}/{max_loops}")

        # Step 2: get sonar issue and list 10 files that has sonar issue.
        unique_files = await asyncio.to_thread(_get_files_with_issues, sonar_tools)
        if not unique_files:
            logger.info("No files with issues found. Stopping workflow.")
            break

        num_files_found = len(unique_files)
        logger.info(f"Step 2: Found {num_files_found} file(s) with issues: {unique_files}")

        # Step 3: select one of the ten files that has sonar issues and has not been processed yet
        target_file = _select_unprocessed_file(unique_files, processed_files)
        if not target_file:
            logger.info("All detected files with issues have been processed in this run. Stopping.")
            break

        logger.info(f"Step 3: Selected file for fix: {target_file}")
        processed_files.add(target_file)  # Mark as processed

        # Step 4: use @rules/Sonar_Issue_Fixing_Protocol.md to fix all sonar issues found in that 1 files
        await _invoke_fix_agent(target_file)



        # Step 6: After sonar issues are fix, run check syntax and fix any pyright issues if found.
        await _check_and_fix_syntax(devops, target_file)

        loops_run += 1

def _finalize_sonar_job(start_time: float, log_id: Optional[int] = None):
    """Helper to finalize the sonar background job execution and report status."""
    duration_ms = int((time.time() - start_time) * 1000)
    active_jobs = getattr(global_state, "active_background_jobs", set())

    # Identify the correct job_name from active jobs or default to "Auto Sonar Issue Fixer"
    job_name = "Auto Sonar Issue Fixer"
    found_job = None
    for name in active_jobs:
        if "sonar" in name.lower():
            found_job = name
            break

    if found_job:
        job_name = found_job
        active_jobs.remove(found_job)

    logger.info(f"Cleaning up active background job '{job_name}' and setting status to Idle.")
    scheduler = getattr(global_state, "scheduler", None)
    if scheduler:
        scheduler._update_task_state(job_name, "Idle")
        if log_id is not None:
            scheduler._log_execution_end(
                log_id,
                "SUCCESS",
                duration_ms,
                response_payload={"message": "Asynchronous execution completed successfully."}
            )

    logger.info("Sonar fix workflow completed.")

async def run_sonar_fix_workflow(log_id: Optional[int] = None):
    start_time = time.time()
    try:
        global_state.settings.reload_models_config()
        sonar_tools = SonarQubeTools(global_state.settings)
        devops = DevOpsTools(global_state.settings)

        # Step 1: run sonar scan then sleep for 10 seconds
        logger.info("Step 1: Running full sonar scan...")
        await asyncio.to_thread(sonar_tools.run_sonar_scan)
        await asyncio.sleep(10)

        # Process the loops via a dedicated helper
        await _process_sonar_fix_loops(sonar_tools, devops)

        # Step 8: Clean up temporary working files
        logger.info("Step 8: Cleaning up temporary working files...")
        await _cleanup_workspace()

    finally:
        _finalize_sonar_job(start_time, log_id)
