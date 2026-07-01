# 🧠 Option 9 Setup Guide: Mnemon Persistent Cross-Session Memory

This guide provides step-by-step instructions for deploying the **Mnemon persistent memory engine** in your ISF-Core environment. Mnemon gives your AI agents long-term memory that survives container rebuilds, restarts, and weeks between conversations.

## Why Use Mnemon?

- **Cross-Session Recall:** Agents remember past bugs, decisions, and commands across sessions — no re-investigating solved problems.
- **Autonomous Knowledge Capture:** After each conversation turn, a background nudge hook judges whether the exchange produced knowledge worth saving, and auto-persists it.
- **Graph-Based Linking:** Insights are linked as a knowledge graph (cause→effect, bug→fix, decision→rationale). Recalling one surfaces the others.
- **Garbage Collection:** Low-importance memories are automatically compacted over time, keeping the graph lean and relevant.
- **Zero External Dependencies:** Runs entirely locally — a Go CLI binary + SQLite wrapped in a lightweight FastAPI container. No cloud, no telemetry, no API keys.

---

## Step 1: Add the Mnemon Container Service

ISF-Core publishes a pre-built `agenticriver/mnemon` Docker image on Docker Hub. Use the standalone compose file to start the service:

```bash
docker compose -f compose.mnemon.yml up -d
```

This single command pulls the `agenticriver/mnemon:main` image and starts the Mnemon container on port 8008 with a persistent named volume for the knowledge graph database.

> **ℹ️ For local development:** If you prefer to build the image locally from source, the `Dockerfile.mnemon` is included in the ISF-Core repository. Run:
> ```bash
> ./build_mnemon.sh --tag v1.0
> ```
> Then update the `image:` tag in `compose.mnemon.yml` to `isf/mnemon:v1.0`.

---

## Step 2: Start the Mnemon Container

```bash
# Pull the pre-built image and start the container
docker compose -f compose.mnemon.yml pull
docker compose -f compose.mnemon.yml up -d
```

Verify the mnemon container is healthy:

```bash
docker compose -f compose.mnemon.yml ps
# Should show "healthy" under STATUS

curl http://localhost:8008/health
# {"insights": 0, "edges": 0, "db_size": "..."}
```

---

## Step 3: Enable Mnemon in ISF-Core

Mnemon is **disabled by default** in a fresh ISF-Core installation. You need to remove it from the skip list and enable the runtime toggle.

### Option A: Via the Web UI (Recommended)

1. Open the ISF-Core Web Workspace and navigate to the **System Health** panel.
2. Under **Core Services**, locate the **Mnemon** row — it will show "Disabled (Skipped)".
3. Click the toggle to **unskip** Mnemon.
   - This automatically enables the runtime toggle and persists the preference.
4. The health status should update to **🟢 Healthy** within a few seconds.

### Option B: Via Configuration Files

1. Edit `backend/.skip_config.json` and remove `"mnemon"` from the `core_skip` array:
   ```json
   {"core_skip": ["sonarqube", "supabase_db_agent", "supabase", "telegram_bot"], ...}
   ```
2. Edit `backend/.ui_prefs.json` and add/set:
   ```json
   {"mnemon_memory_enabled": true}
   ```
3. Restart the `isf-core` container:
   ```bash
   docker compose restart isf-core
   ```

---

## Step 4: Verify Everything Works

Check the health endpoint from inside the `isf-core` container:

```bash
docker compose exec isf-core curl -s http://mnemon:8501/health | python -m json.tool
# Should return: {"insights": N, "edges": N, "db_size": "..."}
```

Open the **System Health** panel in the Web UI and confirm Mnemon shows **🟢 Healthy**.

---

---

# 📝 Tutorial: Cheat Sheet — Prompt Templates

Once Mnemon is enabled, your AI agent has four memory tools. You don't call them yourself — you tell the agent what to do in natural language and it invokes the right tool.

## For Storing Knowledge

| What You Say | What Happens |
|-------------|-------------|
| **"Remember this: [FACT]."** | Stores a single insight into the knowledge graph |
| **"Make a note: [DISCOVERY]."** | Same — persists the discovery for future sessions |
| **"Save this for future sessions: [INSIGHT]."** | Marks the insight as important |
| **"Never forget: [CRITICAL CONSTRAINT]."** | Stores as `critical` — never garbage collected |
| **"Mark this as important: [BUG or FIX]."** | Stores as `high` importance |

**Pro-tip:** Be specific — "the test fails" is worse than "`test_auth.py::test_login` fails with `KeyError: 'token'` because the fixture doesn't mock the JWT decoder."

## For Retrieving Knowledge

| What You Say | What Happens |
|-------------|-------------|
| **"What do we already know about [TOPIC]?"** | Semantic + keyword search across all memories |
| **"Have we encountered [PROBLEM] before?"** | Searches for similar issues from past sessions |
| **"Recap our approach to [FEATURE]."** | Retrieves architectural decisions and rationale |
| **"What was the resolution for [ISSUE]?"** | Finds the bug→fix causal chain |
| **"Search memory for [KEYWORD]."** | Direct keyword search |

## For Linking Related Facts

| What You Say | What Happens |
|-------------|-------------|
| **"Connect [FACT A] to [FACT B]."** | Creates a graph edge between two memories |
| **"Link the [BUG] to its [FIX]."** | Creates a causal edge (bug → fix) |

## For Setting Permanent Constraints

| What You Say | What Happens |
|-------------|-------------|
| **"Global constraint: never [DANGEROUS ACTION]."** | Stored as `critical` — loaded at session start automatically |
| **"Constraint: always [REQUIRED PRACTICE] before [ACTION]."** | Persisted rule the agent checks before acting |

---

# 🎬 Real-World Example: A Complete Workflow

### Session 1 (Monday)

```
👤 You: "The test suite is failing on PR #142. Remember this: test_sonar.py::test_scan
     times out after 120s because the scanner container is slow to start."

🤖 Agent: ✅ Remembered: [causal] test_sonar.py::test_scan times out after 120s
         because the scanner container is slow to start (id=abc123)

👤 You: "I fixed it by increasing the timeout to 300s. Remember the fix."

🤖 Agent: ✅ Remembered: [causal] Increased test_sonar.py timeout to 300s to fix
         scanner startup delay (id=def456)

👤 You: "Link the bug to its fix."

🤖 Agent: ✅ Linked: abc123 --[causal]--> def456
         Future recalls of the bug will automatically surface the fix.
```

### Session 2 (Wednesday — New Container, Fresh Session)

```
👤 You: "Hey, test_sonar.py is failing again. Any ideas?"

🤖 Agent: 🔍 [Mnemon · Recall] Searching knowledge graph...
         
         [MNEMON MEMORY — Cross-Session Graph Recall]
         1. [insight] ⚠️ test_sonar.py::test_scan times out after 120s because the
            scanner container is slow to start
         2. [insight] ⚠️ Increased test_sonar.py timeout to 300s to fix scanner
            startup delay
         
         "Based on our history, this happened on Monday — the SonarQube scanner
          container takes too long to start. We increased the timeout to 300s.
          Did the timeout get reverted, or is the scanner even slower now?"
```

**No re-investigation. No re-explaining. The agent just knows.**

---

# 📊 Memory Types — When to Use Which

| Type | Mnemon Category | Use For | Example |
|------|-----------------|---------|---------|
| **`entity`** | `fact` | Things, people, tools, files | "The skip config file lives at `backend/.skip_config.json`" |
| **`causal`** | `insight` | Cause → effect, bugs → fixes | "PR #142 CI fails because the scanner timeout is too low" |
| **`temporal`** | `context` | Events in time, sequences | "We migrated from Pyright to Ruff on March 15" |
| **`semantic`** | `general` | General facts, definitions | "The project uses PostgreSQL 16 with Supabase" |

---

# 📈 Importance Levels — The Retention Pyramid

```
        ┌──────────┐
        │ critical │  ← NEVER garbage collected. Use for safety rules.
        ├──────────┤
        │   high   │  ← Survives multiple compaction cycles.
        ├──────────┤
        │  medium  │  ← Default. Kept during normal operation.
        ├──────────┤
        │   low    │  ← First to be compacted. Use for trivia.
        └──────────┘
```

---

# 🤖 Pro-Tips: Developing with Mnemon & ISF-Core

### 1. The 2-Minute Rule

> **If you spent more than 2 minutes figuring it out, it's worth remembering.**

Every bug diagnosis, every non-obvious command, every architectural decision — these compound over sessions. A well-maintained Mnemon graph means the agent starts each session already knowing your project's history.

### 2. Let the AI Auto-Capture Knowledge

You don't need to explicitly say "remember this" for everything. Mnemon has a **background nudge hook** that runs after every conversation turn — a fast LLM judges whether the exchange produced knowledge worth saving, and auto-persists it. Just have normal conversations and the agent handles the rest.

### 3. Use Constraints for Safety

If there's something the agent should NEVER do, store it as a `critical` constraint:

```
👤 You: "Global constraint: never run `git push --force` on main."
```

This is loaded at the start of every session automatically — the agent checks constraints before taking any action.

### 4. Query Memory Before Re-Investigating

When you encounter a problem, ask the agent to recall before diving in:

```
👤 You: "Have we seen this error before? What did we do last time?"
```

This saves hours of re-debugging across sessions.
