# Test Fixing Protocol

## Objective
This protocol defines the standard workflow for diagnosing and fixing unit test failures when the tests have fallen out of sync with their associated source code. It applies whenever you are tasked with fixing a failing test. It also documents the full suite of AI agent tools available for testing tasks.

---

## 1. Core Philosophy
When tests fail, do NOT blindly assume the source code is broken. Often, the source code has been updated (e.g., made more robust, signatures changed) but the tests were not updated to reflect these enhancements. Your goal is to ALWAYS align the test expectations with the current, intended behavior of the source code.

---

## 2. Diagnostic Workflow
Whenever you are tasked with fixing a failing test:
1. **Read Both Files:** You MUST ALWAYS read the failing test function AND the corresponding source code function it is testing.
2. **Identify the Disconnect:** Determine *why* the test failed. Look for these common patterns:
   - **Graceful Error Handling:** The source code was updated to catch exceptions (e.g., `try...except`) and return a friendly string message, but the test is still asserting `pytest.raises(Exception)`.
   - **Fallback Mechanisms:** The source code added a fallback (e.g., trying a raw CLI command if a library call fails), but the test mocks do not account for the fallback path.
   - **Return Type Changes:** The source code was updated to return a `Tuple` (e.g., `(result, debug_message)`) instead of a single object, breaking assertions like `assert result is None` (which should now be `assert result[0] is None`).
   - **Signature Changes:** Parameters were added, removed, or renamed in the source function, causing `TypeError` in the test.
   - **React 18.3+ Deprecations:** React 18.3+ has deprecated the `defaultProps` pattern for function components. If tests fail or warn about this, update components to use JavaScript ES6 default parameters instead, and adjust tests if they relied on reading `.defaultProps`.

---

## 3. Strict Test Isolation (The "No Real World" Rule)
When creating or fixing test scripts, AI Agents MUST ensure that the test is completely isolated from external side effects. A test that passes in isolation but fails during a full suite run (6,000+ tests) is usually caused by unmocked global dependencies or network calls causing traffic jams or resource exhaustion.

You MUST actively verify and mock the following before considering a test complete:
- **Global Event Broadcasts:** If the code under test uses things like `broadcast_thought`, WebSockets, or EventBus mechanisms, you MUST patch them (e.g., `patch("backend.core.agentic.agent.broadcast_thought")`). Failing to do so will cause massive network congestion when all tests run simultaneously.
- **External Dependencies:** You MUST mock out system-level dependencies such as `docker.from_env()`, third-party APIs, and File/DevOps tools. Never allow a test to make real outbound socket connections.
- **Fixture Verification:** Check your `pytest` fixtures (like `mock_agent_dependencies`) to ensure that ALL tools and side-effects used by the test subject are properly included in the patches.
- **Environment Variable Leaks:** Test suites must be hardened against host vs. container environments. Use `@mock.patch.dict(os.environ, {"ENV_VAR": "value"}, clear=True)` to prevent active Docker or OS environment variables (like `RUNNING_IN_DOCKER`) from leaking into tests and overriding behaviors.

---

## 4. Resolution Strategy
Once the disconnect is identified, you MUST decide whether to fix the test or the source code:

- **Fix the Test (Most Common):** If the source code changes represent intentional improvements (like graceful error handling or fallbacks), update the test assertions and mocks to match the new behavior.
- **Fix the Source Code (If Accidental Regression):** If the source code accidentally removed a useful parameter (e.g., removing `start_line` / `end_line` for file reading) that the test still verifies, and that functionality is logically still required, restore the functionality in the source code.
- **Delete the Test:** If the test covers a function or class that has been entirely deleted from the source code (because it's obsolete), delete the test.
- **Eliminate Duplicate/Legacy Test Files (Ghost Tests):** If you notice a test file failing aggressively during a full suite run but passing in isolation, check if it's an obsolete duplicate (e.g., `test_agentic.py` vs `test_core_agentic_agent.py`). Obsolete duplicate test files cause mock collisions and `asyncio.run()` event loop crashes. You MUST delete the deprecated file entirely.

---

## 5. Verification
After applying fixes, you MUST:
1. Run `check_syntax` on both the source file and the test file to ensure no Python syntax errors, typing issues (Pyright), or linting violations (Ruff) were introduced (e.g., unused imports).
2. Run the specific test file using the `run_tests` tool to confirm all tests now pass.

🚨 **CRITICAL WARNING:** You MUST ALWAYS pass the specific test filename as `target_path` (e.g., `run_tests("backend/tests/test_git_tools.py")`). NEVER run `run_tests` without a specific test filename, and NEVER use `/run_codebase_testing` or any other codebase-wide test runners. Doing so triggers more than 80+ test scripts concurrently, causing severe timeouts, CPU exhaustion, and extreme delays.

---

## 6. Available AI Agent Testing Tools

The following tools are registered in the AI agent's tool manifest (via `@log_tool_usage` decorators on `TestingTools` in `backend/core/testing_tools/main.py`). You MUST prefer these tools over raw shell commands when performing testing tasks.

### 6.1 `resolve_test_filepath(source_file: str) -> str`
**Purpose:** Instantly determine the exact path where tests for a given source file should reside.

**What it does:**
1. Takes a source file path (e.g., `backend/routers/system.py` or `frontend/src/App.jsx`).
2. Calculates the deterministic flattened path used by the project architecture.
3. Returns the exact test file path (e.g., `backend/tests/test_routers_system.py` or `frontend/tests/src_App.test.jsx`).

**When to use:** Use this tool FIRST when you are asked to "fix the tests" for a specific source file, but you do not know the exact path of the test script.

**Example:**
- 🟢 `resolve_test_filepath("backend/routers/system.py")` — returns `backend/tests/test_routers_system.py`

### 6.2 `generate_unit_tests(source_file: str) -> str`
**Purpose:** Generate a brand-new test file from a source file.

**What it does:**
1. Determines the language and test framework (pytest for Python, vitest/jest for JS/TS).
2. Reads the source code and extracts dependency context.
3. Checks if a test file already exists — if so, runs it first.
4. Uses GenAI (up to 3 attempts) to generate comprehensive unit tests.
5. Picks the best candidate by score (even if not all pass).
6. Writes the test file to disk.

**When to use:** When a source file has NO existing test file, or you need a fresh test suite generated from scratch. This is the PRIMARY tool for the `/generate_unit_test` slash command.

**Example:**
- 🟢 `generate_unit_tests("backend/core/my_module.py")` — creates `backend/tests/test_my_module.py`

### 6.3 `improve_coverage(source_file: str) -> str`
**Purpose:** Analyze coverage gaps in an existing test suite and generate additional tests to fill them.

**What it does:**
1. Runs the existing test suite with coverage instrumentation (`--cov` for Python, `--coverage` for vitest).
2. Parses the coverage report to extract uncovered line numbers.
3. If NO test file exists, delegates to `generate_unit_tests` as a bootstrap.
4. Prompts GenAI with the source code, existing tests, dependency context, AND the specific uncovered lines.
5. Generates an expanded test file that MUST preserve all existing passing tests.
6. Re-runs with coverage to confirm improvement (up to 3 attempts).

**When to use:** When a test file exists but has low coverage, and you want to target specific uncovered lines. This is the PRIMARY tool for the `/improve-test-coverage` slash command.

**Example:**
- 🟢 `improve_coverage("backend/core/data_tools.py")` — adds tests targeting uncovered lines

### 6.4 `run_tests(target_path: Optional[str] = None) -> str`
**Purpose:** Execute test suites with optional coverage paths.

**What it does:**
1. If `target_path` is provided (file or directory), runs only those tests.
2. If `target_path` is `None` or empty, runs the full test suite.
3. Uses unique coverage file paths to avoid collisions between parallel runs.
4. Returns the test output (stdout + stderr) with pass/fail status.

**When to use:** To verify tests pass after manual changes, or to run a specific test file/directory. This is the go-to tool for running tests without the agentic fix loop.

**CRITICAL WARNING:** NEVER call `run_tests()` without a specific `target_path`. Running the entire codebase suite (80+ test scripts) is extremely slow, risks resource exhaustion, and causes timeouts. ALWAYS specify the test file path.

**Examples:**
- ❌ **BAD (NEVER DO THIS):** `run_tests()` (runs the entire test suite - 80+ test scripts, takes too long)
- ❌ **BAD (NEVER DO THIS):** Calling `/run_codebase_testing` or running all tests concurrently
- 🟢 `run_tests("backend/tests/test_git_tools.py")` — runs a specific test file
- 🟢 `run_tests("backend/tests/test_system.py")` — runs all tests in that specific file

### 6.5 `fix_e2e_test(test_file_path: str) -> str`
**Purpose:** Auto-diagnose and fix failing Playwright E2E tests with browser-based self-healing.

**What it does:**
1. Runs the Playwright E2E test using `./frontend/run_e2e.sh`.
2. If it fails, captures the error output and uses Playwright MCP tools (`browser_snapshot`, `browser_console_messages`) to inspect the page state.
3. Feeds the DOM snapshot, console errors, and test code to GenAI for diagnosis.
4. Applies the fix and re-runs (up to 3 attempts).

**When to use:** When a Playwright E2E test (`.spec.js`) is failing and needs self-healing. NOT for unit tests.

**Example:**
- 🟢 `fix_e2e_test("tests/agent_intent_display.spec.js")` — auto-fixes a failing E2E test

### 6.6 `run_static_analysis(file_path: str) -> List[str]`
**Purpose:** Run linting and static analysis on a file.

**What it does:**
1. Runs the appropriate linter for the file type (Ruff+Pyright for Python, ESLint for JS/TS).
2. Returns a list of detected issues.

**When to use:** Before committing changes, to catch linting violations or type errors that `check_syntax` might miss. Complementary to `check_syntax`.

**Example:**
- 🟢 `run_static_analysis("backend/core/my_module.py")` — returns list of lint/type issues

---

## 7. Tool Decision Matrix

| Scenario | Use This Tool |
|---|---|
| I need to find the exact test path for a source file | `resolve_test_filepath` |
| A source file has NO test file yet | `generate_unit_tests` |
| A test file exists but coverage is low | `improve_coverage` |
| I just made manual changes and want to verify | `run_tests("backend/tests/specific_test.py")` (NEVER run without target file) |
| An E2E Playwright test is broken | `fix_e2e_test` |
| I want to check for lint/type errors before committing | `run_static_analysis` or `check_syntax` |

---

## 8. Examples

### 🟢 Good Examples
* **Good:** Changing `with pytest.raises(GitCommandError):` to `assert "Failed to get diff" in result` when the source code now handles the error gracefully.
* **Good:** Adding mocks for a newly introduced CLI fallback path in tests where the primary library call is mocked to fail.
* **Good:** Updating `assert result` to `assert result[0]` when a function's return type changes to a Tuple.
* **Good:** Calling `generate_unit_tests("backend/core/new_module.py")` for a module with zero test coverage.
* **Good:** Calling `run_tests("backend/tests/test_git_tools.py")` after manually fixing a test to verify it passes.
* **Good:** Adding `@patch("backend.core.agentic.agent.broadcast_thought")` to ensure the test does not spam the real event bus during a full test suite run.

### 🔴 Bad Examples
* **Bad:** Blindly commenting out failing tests without investigating.
* **Bad:** Reverting robust error handling in the source code just to make an old test pass.
* **Bad:** Modifying test code without reading the actual source code to see what it currently does.
* **Bad:** Running raw `pytest` shell commands when the `run_tests` tool is available (it handles coverage path isolation).
* **Bad:** Using `generate_unit_tests` when a test file already exists and just needs a fix — use `improve_coverage` instead.
* **Bad:** Calling `run_tests()` without arguments, running `/run_codebase_testing`, or triggering codebase-wide testing without specifying a test file (this runs 80+ test scripts, taking a massive amount of time).
* **Bad:** Leaving `DockerTools` unmocked, causing the test to open a real outbound network socket to the local Docker Engine gateway.
