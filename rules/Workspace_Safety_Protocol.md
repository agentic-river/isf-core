# 🛡️ Workspace Safety Protocol

## Part 1: Workspace Safety & Anti-Destruction

### Never Move/Delete Root Directories
You are STRICTLY FORBIDDEN from running `mv`, `rm -rf`, or moving critical root directories (such as `supabase-docker`, `.git`, `backend`, `frontend`) to temporary locations or inside `node_modules`.

### Scanner EACCES Workarounds
If a tool like `sonar-scanner` fails due to `EACCES` (Permission Denied) on a directory, do NOT attempt to move or hide the directory. Stop the task, report the OS permission error to the user, and ask for guidance.

### Explicit Consent
Any `rm` command targeting a directory requires explicit, written consent from the user.

### Destructive Git Commands
You are STRICTLY FORBIDDEN from running ANY of the following without explicit user approval in the current chat session:
- `git restore <file>` or `git restore .`
- `git checkout -- <file>`
- `git reset --hard`
- `git clean -fd`
- `git stash drop` / `git stash pop` (on stashes you did not create)
- `git rebase --abort` / `git merge --abort` (on operations you did not start)

These commands silently discard uncommitted changes that may belong to:
- Another active AI chat session (different browser tabs may stream to different AI instances)
- The background cron tasks (`cron_tasks/test_coverage_task.py`, `cron_tasks/sonar_fix_task.py`, `cron_tasks/auto_agent_task.py`) which autonomously modify files for coverage improvements, SonarQube fixes, and background agent work
- The user's own in-progress IDE edits (VS Code)

### Pre-Destructive Safety Check
Before ANY git write operation, you MUST:
1. Run `git status --porcelain` to check for uncommitted changes
2. Run `git stash list` to check for existing stashes
3. If changes exist that you did NOT create in this session, STOP and ask the user

### Concurrent Session Awareness
This workspace may have MULTIPLE AI agents operating simultaneously:
- **Chat sessions:** Different browser tabs may stream to different AI instances
- **Cron tasks:** Background jobs registered via the admin scheduler periodically run autonomous AI agents that read, modify, and write files:
  - `test_coverage_task.py` — Runs `improve_coverage` / `generate_unit_tests` on low-coverage files
  - `sonar_fix_task.py` — Fetches SonarQube issues and applies fixes
  - `auto_agent_task.py` — Processes chat sessions flagged with `?` / `!` tags for background execution
- **User edits:** The user may be editing files in their IDE (VS Code)

**Before assuming a file is safe to modify or revert:**
- Check `get_current_diff` to see who made recent changes
- If a file has been modified in the last 60 seconds, assume a concurrent session is active
- Never `git restore` a file that has uncommitted changes you did not author in this session
- The QA Hallucination Gate (`_check_hallucinated_completion`) already cross-checks your completion claims against `git diff` baselines — falsely claiming changes will be rejected with a strike
