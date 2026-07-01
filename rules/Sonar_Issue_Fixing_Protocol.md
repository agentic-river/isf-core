# Sonar Issue Fixing Protocol

## Objective

This protocol defines the mandatory workflow for AI agents when tasked with fetching and fixing SonarQube code issues. It ensures issues are correctly identified from the shadow project, fixed, and verified through re-scanning.

---

## 1. Core Principles

- **Shadow First:** After a focused `run_sonar_scan`, fresh issues are in the Shadow Project (`_focus`), NOT the Main Project. Always use `get_sonar_issues_by_filename` which queries shadow-first.
- **No Scan, No Issues (False-Clean):** An empty issue list from `get_sonar_issues_by_filename` is only valid *after* a successful `run_sonar_scan` has been run and processed. If a file has not been scanned and uploaded yet, the fetch tool will return `[]`, which is a false-clean result.
- **Verify Fixes:** You MUST re-scan and re-fetch after fixing. Never assume a fix worked because the code looks right — let SonarQube confirm.
- **Wait After Scan:** SonarQube needs 5-10 seconds to process an uploaded analysis. Always wait before querying issues from a fresh scan.
- **Minimize Changes:** Only fix the reported issues. Do NOT refactor unrelated code, change public APIs, or alter business logic unless the Sonar issue specifically demands it.

---

## 2. Mandatory Workflow: Scan → Fetch → Fix → Re-scan → Verify

### Step 1: Scan the File

```
run_sonar_scan(files_to_scan=["path/to/file.py"])
```

- This uploads to the **Shadow Project** (`ai_developer_pro_focus`).
- Full project scans (no arguments) go to the **Main Project** — don't use those for focused fixing.

### Step 2: Wait for Server Processing & Progress Reporting

Wait **5-10 seconds** after the scan completes. The SonarQube server needs time to process the uploaded analysis report before issues become queryable.

- **Progress Tracking:** Always use the `report_progress` tool to log that the Sonar scan has been executed and that you are waiting for processing (e.g., `status="processing"`, `details="Executed Sonar scan, waiting 5-10 seconds for SonarQube to complete analysis..."`). This keeps the user informed and prevents the UI from appearing idle.

### Step 3: Fetch Issues

```
get_sonar_issues_by_filename("path/to/file.py")
```

- Returns a list of dicts with `severity`, `line`, `message`, `type`, `key`.
- Returns `[]` if no unresolved issues exist.
- **CRITICAL WARNING - False-Clean State:** Returning `[]` (an empty list) at the start does **not** necessarily mean there are no issues in the file. It can mean the file was never scanned and uploaded, so Sonar has no record of it. You **MUST** run `run_sonar_scan` first to ensure the code is uploaded and analyzed before concluding that a file has no issues.
- **Shadow-first query:** This method queries the Shadow Project first. If the shadow query succeeds (even if it returns 0 issues because all are fixed), it returns the result immediately. It ONLY falls back to the Main Project if the shadow query fails (e.g., file never scanned in shadow project).

### Step 4: Analyze and Fix

For each issue:

| Issue Type | Common Fix Strategy |
|---|---|
| **Cognitive Complexity** (>15) | Extract helper methods to reduce nesting/branching. Each helper should have a single responsibility. |
| **Bug (e.g., unused variable, potential null)** | Add null guards, remove dead code, fix logic errors. |
| **Code Smell (e.g., too many params, long method)** | Extract parameter objects, split long methods. |
| **Duplication** | Extract shared logic into a utility function. |

**Critical rules during fixing:**

1. Read the file **before** modifying it — never assume current content from memory.
2. Prefer `smart_replace` over `write_file_content` for large files to save tokens.
3. Maintain the EXACT same public API signatures unless the Sonar issue demands a change.
4. After fixing, run **both** `check_syntax` AND `run_tests` (ALWAYS specifying the specific test file name as `target_path` to avoid running all 80+ codebase tests) on the file to catch regressions.
5. If the file has no existing tests, verify call sites aren't broken by checking callers.

### Step 5: Re-Scan

```
run_sonar_scan(files_to_scan=["path/to/file.py"])
```

Upload fresh code to the Shadow Project. Wait 5-10s again.

### Step 6: Verify

```
get_sonar_issues_by_filename("path/to/file.py")
```

- **Expected:** `[]` (empty list) — all issues resolved.
- **If issues remain:** Go back to Step 4 and fix remaining issues.
- **If the same issue persists:** Read `get_sonar_issue_details("path/to/file.py:<line>")` for the specific rule's fix guidance. The `fix_guidance` field often explains exactly what the rule expects.

### Step 7: Clean Up Temporary Files

After all fixes are verified, you MUST remove any temporary working files created during the session:

- Delete any test scripts, debug logs, or intermediate artifacts you wrote.
- Do NOT delete production code, configuration files, or persistent data (e.g., `.browser_sessions/*.json`).
- Use `execute_shell_command` with `rm` to remove files, or `git checkout` to revert unintended changes.

---

## 3. Understanding Issue Types

| Sonar Type | Meaning | Priority |
|---|---|---|
| `BUG` | Code that will likely break at runtime | Fix immediately |
| `VULNERABILITY` | Security-sensitive code | Fix immediately |
| `CODE_SMELL` | Maintainability issue (complexity, duplication, etc.) | Fix, but safe changes only |
| `HOTSPOT` | Security-sensitive code that needs manual review | Flag for human review |

| Sonar Severity | Meaning |
|---|---|
| `BLOCKER` | Will crash or cause data loss |
| `CRITICAL` | Severe maintainability or potential bugs |
| `MAJOR` | Significant impact on maintainability |
| `MINOR` | Minor quality issue |
| `INFO` | Advisory finding |

---

## 4. Common Sonar Issues & Fix Patterns

### 4.1 Cognitive Complexity (`CODE_SMELL`)

**Message:** "Refactor this function to reduce its Cognitive Complexity from X to the 15 allowed."

**Fix Strategy — Extract Helper Methods:**

```python
# ❌ Bad: Monolithic function with nested branches
def send_telegram(msg, loop, bg_set):
    for x in thing:
        if x.startswith("@"):
            # 10 lines of parsing
            ...
    if loop:
        # 15 lines of scheduling
        ...

# 🟢 Good: Thin orchestrator + single-responsibility helpers
def send_telegram(msg, loop, bg_set):
    chat_id = _get_chat_id()
    notify_msg = _build_notify_message(msg, chat_id)
    _send_and_map_message(chat_id, notify_msg)
    _schedule_background_coro(bg_set, loop, chat_id)

def _get_chat_id(): ...
def _build_notify_message(msg, chat_id): ...
def _send_and_map_message(chat_id, notify_msg): ...
def _schedule_background_coro(bg_set, loop, chat_id): ...
```

### 4.2 Unused Imports / Variables (`CODE_SMELL`)

**Fix:** Remove the unused import or variable. Run `check_syntax` afterward to confirm no side effects.

### 4.3 Bare Except (`CODE_SMELL`)

**Message:** "Catching Exception is too broad."

**Fix:** Narrow the exception type to the specific exception(s) expected:

```python
# ❌ Bad
except Exception:
    pass

# 🟢 Good
except (ValueError, KeyError) as e:
    logger.warning(f"Expected error: {e}")
```

### 4.4 Duplicate String Literals (`CODE_SMELL`)

**Fix:** Extract repeated strings into module-level constants.

### 4.5 Deprecated React `defaultProps` (`CODE_SMELL` / Warning)

**Message:** "Support for defaultProps will be removed from function components in a future major release."

**Fix:** React 18.3+ has deprecated the `defaultProps` pattern for function components. Remove `.defaultProps` definitions and use JavaScript ES6 default parameters in the component signature instead.

---

## 5. Tool Integration

The Sonar fixing workflow integrates with other AI agent tools:

| Tool | When to Use |
|---|---|
| `get_sonar_issues_by_filename` | Fetch issues for a specific file (Step 3, Step 6) |
| `get_sonar_issue_details` | Get fix guidance for a persistent issue |
| `get_sonar_issues_by_severity` | Get a high-level overview of project-wide issues |
| `run_sonar_scan` | Upload fresh analysis (Step 1, Step 5) |
| `get_quality_gate_status` | Check main project quality gate (NOT for shadow verification) |
| `check_syntax` | Verify no type/lint errors after fixing |
| `run_tests` | Verify no regressions after fixing (ALWAYS pass the specific test file name as `target_path` to avoid running all 80+ test scripts and causing timeouts) |

---

## 6. Anti-Patterns (NEVER)

- 🔴 **Never** assume an empty list `[]` means zero issues without running `run_sonar_scan` first. An unscanned file has no recorded issues on the Sonar server, which creates a false sense of security (false-clean state).
- 🔴 **Never** assume a fix worked without re-scanning and verifying with `get_sonar_issues_by_filename`.
- 🔴 **Never** call `get_sonar_issues_by_filename` immediately after `run_sonar_scan` without waiting 5-10s.
- 🔴 **Never** use `get_quality_gate_status` to verify a focused scan fix — it only checks the Main Project.
- 🔴 **Never** blindly refactor a function to reduce complexity if it changes the public API or business logic.
- 🔴 **Never** leave placeholders or TODOs after a fix — the fix must be complete.
- 🔴 **Never** introduce new Pyright type errors or Ruff warnings while fixing Sonar issues.
- 🔴 **Never** call `run_tests` without a specific test filename as `target_path`. Running the entire codebase suite (80+ test scripts) concurrently will cause severe timeouts, resource exhaustion, and block development.
- 🔴 **Never** leave temporary scripts, debug files, or intermediate artifacts in the workspace after completing a fix session. Always clean up before finishing.
- 🔴 **Never** strip module prefixes from Python coverage XML paths (e.g., `backend/core/file.py` → `core/file.py`). The `sonar.python.coverage.reportPaths` property is set at the project root level — not per-module. Stripping the prefix causes SonarQube to resolve `/app/core/file.py` instead of `/app/backend/core/file.py`, resulting in 0% coverage for all Python modules. See `docs/Sonar_Tools_And_Workflow.md` §6 for the full pipeline explanation.

---

## 7. Examples

### 🟢 Good Examples

- **Good:** `run_sonar_scan(files_to_scan=["backend/services/foo.py"])` → wait 10s → `get_sonar_issues_by_filename("backend/services/foo.py")` → finds 1 CRITICAL on line 42 → extracts helper methods → `check_syntax` + `run_tests` pass → `run_sonar_scan` → wait 10s → `get_sonar_issues_by_filename` returns `[]` ✅.
- **Good:** Fixing cognitive complexity by extracting 3 helpers, each under 10 lines with a single responsibility, while keeping the original function signature unchanged.
- **Good:** Reading `get_sonar_issue_details` for a persistent issue to understand the rule's exact expectation before attempting a second fix.

### 🔴 Bad Examples

- **Bad:** Running `run_sonar_scan()` (full project, no arguments) and then trying to query `get_sonar_issues_by_filename` expecting shadow results. Full scans go to Main.
- **Bad:** Making a fix, declaring "done," and never re-scanning to verify.
- **Bad:** Introducing `from typing import Any` without actually using it, triggering a new Ruff `F401` warning.
- **Bad:** Refactoring an entire file because of one cognitive complexity issue on one function.
