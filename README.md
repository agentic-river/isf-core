# 🤖 ISF-Core — Infinite Software Factory

<p align="center">
  <em>The Free, Self-Hosted, Web-Based AI App Factory. Coordinate a concurrent team of specialized AI workers in a unified "Inbox-style" workspace. Built for maximum token efficiency, self-learning, and 100% data privacy.</em>
</p>

<p align="center">
  <a href="https://github.com/agentic-river/isf-core/stargazers"><img src="https://img.shields.io/github/stars/agentic-river/isf-core?style=for-the-badge&color=yellow" alt="Stars" /></a>
  <a href="https://github.com/sponsors/agentic-river"><img src="https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink?style=for-the-badge&logo=github" alt="Sponsor" /></a>
  <a href="https://github.com/agentic-river/isf-core/issues"><img src="https://img.shields.io/badge/Feedback-Welcome-brightgreen?style=for-the-badge" alt="Feedback" /></a>
</p>

Welcome to your standalone deployment of **ISF-Core**, the engine behind the **Infinite Software Factory (ISF)**. ISF-Core is a free, self-hosted, local-first AI development platform that transforms you from a _writer of code_ into an _Orchestrator of AI Departments_.

Unlike traditional terminal-bound CLI tools or editor-integrated extensions that force you into a single-threaded bottleneck, ISF-Core lets you act as the **Engineering Manager**, orchestrating specialized, concurrent AI workers via an Outlook-style, multi-threaded Web UI dashboard.

---

## 📟 The Competitive Landscape: Terminal CLI vs. Web GUI

To understand why ISF-Core represents a major evolution in AI-driven development, let's examine how it stacks up against standard market tools:

| Feature / Metric         | 📟 Terminal CLI Agents                                                 | 🔧 API-Only Foundations                                      | 💻 Editor-Bound Chat Extensions                                  | 🌐 ISF-Core                                                                   |
| :----------------------- | :--------------------------------------------------------------------- | :----------------------------------------------------------- | :--------------------------------------------------------------- | :---------------------------------------------------------------------------- |
| **Interface Mode**       | **Terminal CLI Only**                                                  | **API-Only (No UI)**                                         | **IDE-Bound GUI**                                                | **Web-Based Workspace UI**                                                    |
| **User Experience (UX)** | Raw terminal log streams; hard to track parallel files.                | None. Requires building a custom frontend or script wrapper. | Inline edits & sidebars. Hard to run multiple independent tasks. | **Inbox Dashboard (Outlook-style)** with thread-switching & notifications.    |
| **Concurrency**          | **Sequential.** Stalls your shell while executing single loops.        | Multi-thread capable but requires custom coordination.       | **Sequential.** One inline edit or chat prompt runs at a time.   | **Concurrent.** Spin up multiple specialized agents in parallel.              |
| **Token Efficiency**     | **Low.** Frequently re-reads entire file structures and terminal logs. | **Low.** Zero built-in caching; client must manage context.  | **Moderate.** Employs semantic RAG, but context grows rapidly.   | **Ultra-High.** Local AST maps ensure only micro-snippets are sent.           |
| **Self-Healing Loop**    | Requires user copy-pasting shell commands or manual runs.              | Manual setup.                                                | User must trigger test terminal or run manually.                 | **Fully Autonomous.** Core executes tests & repairs errors behind the scenes. |
| **Hosting & Privacy**    | Local, but depends on hosted cloud engine constraints.                 | Proprietary cloud API.                                       | Hosted cloud wrapper; potential privacy concerns.                | **100% Private, Self-Hosted Docker.** Your key, your code.                    |

---

## ⚡ The ISF-Core Paradigm: You are the Engineering Manager

```
                         ┌─────────────────────────┐
                         │   YOU: Eng. Manager     │
                         └───────────┬─────────────┘
                                     │ (Coordinates & Approves)
                                     ▼
         ┌───────────────────────────┴───────────────────────────┐
         │              ISF-CORE INBOX WORKSPACE                 │
         │   (Parallel, Threaded Communication & Output)         │
         └───────┬───────────────────┬───────────────────┬───────┘
                 │                   │                   │
                 ▼                   ▼                   ▼
        ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
        │    Architect    │ │  Code Learner   │ │  Senior Coder   │
        │ (Design Spec)   │ │ (Reads Legacy)  │ │ (Writes Code)   │
        └─────────────────┘ └─────────────────┘ └─────────────────┘
```

- **Manager-Worker Paradigm:** You do not spend hours writing exhaustive, perfect prompts. You delegate high-level requirements. Your specialized AI workers collaborate in parallel, presenting clear options and design proposals for your approval.
- **Concurrent Multi-Agent Execution:** Need to refactor a backend API while drafting a frontend view? Spin up parallel workers. While Agent A reads and maps legacy files, Agent B outlines the API schema, and Agent C designs frontend components concurrently.
- **Outlook-Style Multi-Threaded Workspace:** Interact with your team through an elegant web-based messaging hub. Monitor progress, review code proposals, adjust workflows, and make high-level decisions across parallel tasks without context switching or terminal freezing.

---

## 🧠 Core Differentiators & Breakthrough Capabilities

### 1. Radical Local Token Efficiency (No Context Bloat)

Most agentic systems suffer from "context bloat," blindly dumping massive file structures into expensive LLM prompts. ISF-Core proves its token efficiency through measurable, real-time observability and architectural routing:

- **Token Usage Dashboard:** A dedicated `/usage` analytics page visually graphs your daily input/output token consumption, exact micro-costs, and provider breakdowns so you are never surprised by API bills.
- **Message-Level Transparency:** Every chat message displays a localized usage bar showing the exact model used, input/output token counts, fractional dollar cost, and even DeepSeek KV Cache Hit/Miss metrics.
- **Role-Based Model Routing (`models.yaml`):** Not every task needs an expensive reasoning model. We define explicit agent roles in `models.yaml` (e.g., `coder`, `planner`, `sonar_fixer`, `rule_grader`) allowing high-frequency cron jobs and background daemon tasks to automatically route to ultra-cheap, fast models (like `gemini-flash-lite`), while reserving frontier models (like `deepseek-v4-pro`) only for complex architectural tasks.

### 2. Local-First Web Dashboard + Any IDE

Unlike IDE-bound extensions that trap you inside a single editor pane or terminal CLI tools that freeze your shell with sequential loops, ISF-Core provides a **full-featured Web-Based Workspace dashboard** at `http://localhost:3006` that collaborates with your development IDE through a shared filesystem:

- **Zero-Sync Filesystem Mirroring:** The entire project directory, including `.git`, is mounted as a Docker volume. When the AI writes code, it writes directly to your actual workspace files — VS Code, IntelliJ, or any editor instantly sees every change. When you edit a file manually, the AI sees it immediately. No copy-paste, no cloud upload, no deployment step.
- **Interactive File Explorer & Code Editor:** A resizable sidebar with a git-aware file tree (modified files highlighted), file search, and a built-in syntax-highlighted editor supporting 30+ languages — edit files directly in the browser and save to disk with `Ctrl/Cmd + S`.
- **Outlook-Style Multi-Threaded Inbox:** Switch between concurrent AI agent chat threads like email — each thread operates independently, with status tagging, archive/trash, deep search, and notification badges when background tasks complete.
- **Visual Thinking Process Dashboard:** A full-screen expandable panel traces every tool call with color-coded icons (reasoning 🟣, progress 🟡, steering 🔵, success 🟢, error 🔴), a progress bar, and a duration timer — giving you complete transparency into the agent's decision-making.
- **Dry Run Mode:** Toggle with `Shift + Tab` to instruct the AI to plan and propose changes without writing to disk — perfect for code review, architectural discussion, or when you prefer to apply changes manually in your IDE.
- **Runtime Model Switching:** Swap LLM providers and models on the fly from a dropdown menu while chatting — no restart required, no config file edits.

> 💡 **The result:** Your IDE and your AI tool (ISF-Core) are not competitors — they're collaborators sharing one filesystem. Work on Plan -> Execute in the Web UI, review git changes in VS Code. No cloud upload, no sync step, no copy-paste — full data sovereignty with zero friction between your IDE and your ai agents.

### 3. Choice of Leading-Edge LLM Powerhouses

ISF-Core provides native out-of-the-box support for **7 LLM providers** spanning 39+ registered models, allowing you to swap backends dynamically depending on your active task:

- **Gemini LLM API:** Unlock the massive **2-million token context window** and high-speed execution. Gemini is the ultimate choice for deep visual inspections of browser snapshots (via Playwright), ingesting massive codebase directory architectures at once, and generating embeddings.
- **Anthropic Claude API:** Access **Claude 4 Opus, Sonnet, and Haiku** — Anthropic's frontier reasoning models with exceptional coding, analysis, and creative capabilities.
- **DeepSeek V4 LLM API:** Leverage state-of-the-art coding reasoning and architectural planning at a fraction of the cost. DeepSeek V4 Pro and Flash are highly optimized for precise logical deduction, self-healing code edits, and structured outputs.
- **OpenAI API:** Standard connectivity to GPT-4 and other OpenAI models for general-purpose reasoning and code generation.
- **Alibaba Qwen API:** Tap into the **Qwen3.7 Max/Plus/Flash** family and **GLM-5.1** — high-performance models with competitive benchmarks for coding, multilingual tasks, and long-context understanding.
- **Kimi (Moonshot) API:** Unlock **Kimi K2.7 Code** with a **256K context window** and always-on chain-of-thought reasoning, purpose-built for complex code generation and debugging.
- **Ollama (Local):** Run **Gemma 4 26B** entirely on your own hardware via Ollama — zero API costs, 32K context, and full data sovereignty for air-gapped or sensitive environments.

### 4. Self-Reflection & Auto-Optimizing Rules

Unlike other engines that repeat the same errors in an infinite loop, ISF-Core features **Meta-Learning Self-Reflexivity**:

- When a worker encounters a build error, a failing unit test, or an architectural mistake, the orchestrator triggers an automated **Post-Mortem Analysis**.
- The system analyzes why the mistake happened, designs a corrective workflow, and **writes a new markdown rule directly into your local `rules/` directory** (e.g., `rules/API_Naming_Conventions.md`).
- In subsequent tasks, the AI reads these rules dynamically, ensuring the factory permanently adapts to your specific codebase constraints and never repeats a mistake.

### 5. Living, Continuous Documentation Updates

Legacy codebase documentation is notoriously prone to decay. ISF-Core treats documentation as a first-class citizen:

- As your coder agents modify databases, refactor modules, or create schemas, a specialized **Technical Writer Agent** immediately updates relevant markdown files inside your `docs/` directory.
- This ensures that both you (the human director) and future AI worker threads always have an accurate, high-fidelity map of the active system layout.

### 6. Continuous Maintenance Department (Autonomous Cron Workflows)

In a high-performing software engineering department, development doesn't stop when humans log off. Maintenance and code health are continuous. ISF-Core embeds this professional engineering culture directly into its self-hosted architecture via its integrated **Cron Daemon**:

- **Routine Code Cleanups:** Schedule background jobs at any interval (e.g., nightly, hourly) that act as your persistent code hygiene department.
- **Autonomous Test Fixing:** A dedicated background agent runs your test suites, intercepts test failures, diagnoses the root causes, and patches broken test scripts or application regressions autonomously.
- **Sonar Quality Code Correction:** The scheduled workflow runs static analysis scans, fetches quality issues, and refactors complex functions, unused variables, and code smells without requiring manual intervention.
- **Security Hotspot Defusing:** Routine audits scan your codebase for exposed credentials, loose API schemas, and insecure practices, applying secure, compiled refactoring blocks.
- **Test Coverage Maximization:** Background tasks analyze test gaps using local coverage reports, writing brand-new unit or integration test cases targeting untested lines to raise coverage scores automatically over time.

---

## 🛠️ Architecture Design

### System Workflow

The flowchart below illustrates how the **Web Dashboard** interacts with the **ISF Core - Orchestration Engine** and local files, keeping your credentials, data, and code private.

```
                  ┌─────────────────────────────────────────┐
                  │        WEB-BASED BROWSER WORKSPACE      │
                  │   - Outlook-Style Inbox & Threads       │
                  │   - Interactive Process Cards & Charts  │
                  └────────────────────┬────────────────────┘
                                       │ (WebSockets & APIs)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      DOCKER CONTAINER isf/factory       │
                  │                                         │
                  │   ┌─────────────────────────────────┐   │
                  │   │        Pre-Compiled Core        │   │
                  │   │      (Orchestration Engine)     │   │
                  │   └────────────────┬────────────────┘   │
                  │                    │                    │
                  │                    ▼                    │
                  │   ┌─────────────────────────────────┐   │
                  │   │   Concurrent Micro-Workers      │   │
                  │   │  - Architect   - Code Learner   │   │
                  │   │  - Senior Coder - QA Specialist │   │
                  │   └────────────────┬────────────────┘   │
                  └────────────────────┼────────────────────┘
                                       │ (Local volume mapping)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │         LOCAL USER WORKSPACE            │
                  │   - browser-agents/       - rules/      │
                  │   - data/ (SQLite)        - docs/       │
                  └─────────────────────────────────────────┘
```

### Self-Healing & Verification Loop

The sequence map shows how ISF-Core self-corrects and learns from compiler/test output before presenting the results to the manager:

```
 User (Web UI)        Inbox Orchestrator         Specialized Agent         Local Compiler / Test
      │                       │                         │                           │
      │── 1. Create Task ───> │                         │                           │
      │   "Refactor API"      │── 2. Local AST Analysis │                           │ (Tree-Sitter parses layout
      │                       │      & Code Snippets    │                           │  locally; sends <5% context)
      │                       │────────────────────────>│                           │
      │                       │   (Micro-Task Prompt)   │                           │
      │                       │                         │── 3. Edit Target File ───>│ (Writes directly to volume)
      │                       │                         │                           │── 4. Run Self-Healing Test
      │                       │                         │<── 5. Parse Build Logs ───│ (No LLM token copy-paste!)
      │                       │                         │                           │
      │                       │                         │── 6. Self-Reflect Error ─>│ (Mistake detected!)
      │                       │                         │   (Writes rule to rules/) │
      │                       │<── 7. Task Completed ───│                           │
      │<── 8. AI Response / ──│                         │                           │
      │    Green Notification │                         │                           │
```

---

## Prerequisites

Before getting started, ensure your system meets the following requirements:

1. **Operating System:** Windows 11 with WSL2 (Ubuntu) OR macOS (M1 chip or later)
   - **RAM:** At least 16 GB (recommended)
   - **Storage:** At least 10 GB free SSD space (recommended)
2. **Docker Desktop:** Installed and running
   - _Tip: We highly recommend increasing your Docker Desktop resource limits (at least 4-6 dedicated CPU cores and 8GB+ RAM) to ensure the AI orchestration engine and parallel workers run smoothly._
3. **Git:** Installed
4. **Python:** 3.12 (recommended)

## 🚀 Quick Start

Ensure you have [Docker](https://docs.docker.com/get-docker/) installed, then launch your factory in seconds:

```bash
# Clone the orchestration repository (scaffolding & workspace only) to a new project folder:
git clone https://github.com/agentic-river/isf-core.git my-new-project
cd my-new-project

# Remove the existing Git history:
rm -rf .git

# Initialize a new Git repository:
git init
git add .
git commit -m "Initial commit: Scaffolding from ISF-Core"

# Set up your AI Proxy environment credentials
cp .env.ai_proxy.example .env.ai_proxy

# Open .env.ai_proxy and add your Gemini, DeepSeek, or other API keys
nano .env.ai_proxy
# or use VSCode
code .env.ai_proxy

# Run the automated setup script to configure your environment, database, and settings
python setup.py

# 🚀 Start ISF-Core + AI-Proxy Docker containers together (recommended)
python start_isf_core.py
```

Access your interactive workspace dashboard at `http://localhost:3006`!

> 🛑 **To shut down later:** Run `python shutdown_isf_core.py`
> 🔧 **To start the AI-Proxy standalone:** Run `docker compose -f ai-proxy.yml up -d`

### 🔐 Why AI-Proxy Is Separate from ISF-Core

You'll notice this deployment includes **two** containers:

| Container  | Purpose                                                                   |
| ---------- | ------------------------------------------------------------------------- |
| `isf-core` | The factory engine — orchestrates agents, manages workflows, stores data  |
| `ai-proxy` | A dedicated LLM gateway — routes requests to Gemini, DeepSeek, and OpenAI |

**This separation is intentional and critical for security:**

- **API Key Isolation:** Your LLM provider keys (`GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, etc.) live **only** inside the `ai-proxy` container via `.env.ai_proxy`. The `isf-core` container never sees them. If the factory is ever compromised, your keys are not exposed.
- **Infrastructure Boundary:** In production or team environments, the `ai-proxy` can run on a separate machine with restricted network access, while `isf-core` runs on developer workstations. The proxy is a single choke-point for auditing and rate-limiting LLM usage.
- **Independent Scaling:** The ai-proxy can be scaled horizontally (multiple instances behind a load balancer) without touching the factory engine.
- **Provider Rotation:** Switching LLM providers or rotating keys requires restarting only the proxy — not the entire factory.

> 💡 **Best Practice:** Keep `.env.ai_proxy` in your host's secure filesystem. Never commit it to version control (it's already in `.gitignore`).

---

## 🗺️ Tour Guide

Once you have successfully started ISF-Core, we highly recommend checking out our UI Tour Guide to familiarize yourself with the dashboard and verify your AI connections.

👉 **[View the ISF-Core UI Tour Guide](options_setup/TourGuide.md)**

---

## 📂 Cloned Workspace Architecture

Once the repository is cloned, your local workspace mapping matches the root folder containing your container management configs:

| Directory / File       | Purpose                                                                                                                                                                                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/`                | Living system documentation. **The AI automatically keeps these updated** so your project context never drifts.                                                                           |
| `rules/`               | Strict operational guidelines. **The AI writes post-mortem rules here** to optimize its future development workflow!                                                                      |
| `backend/tasks/`       | Python scripts for scheduled background maintenance jobs (cron routines that autonomously fix failing tests, resolve Sonar issues, defuse security hotspots, and expand test coverage).   |
| `browser-agents/`      | Browser automation scripts for interacting with external web portals.                                                                                                                     |
| `supabase-docker/`     | Self-hosted Supabase/PostgreSQL Docker configs — compose stack (Kong, Auth, Postgres, Studio), canonical schema init SQL, and migration scripts. Used by Option 1 to scale beyond SQLite. |
| `data/`                | Your local SQLite database (`chat_history.db`) and persistent AI data — stored securely on your host machine.                                                                             |
| `system_prompt.md`     | The AI's core behavioral constitution — defines tool-use protocols, mandatory self-review, anti-hallucination rules, visualization standards, and workspace safety constraints.           |
| `models.yaml`          | LLM model registry (39+ models, 7 providers) with per-token costs and **role-based routing** — cheap models for cron/background tasks, frontier models for complex architecture.          |
| `setup.py`             | Automated first-run setup: creates `.env`, `.env.ai_proxy.example`, initializes SQLite schema, and writes default skip config. **Run once before starting.**                              |
| `start_isf_core.py`    | One-command launcher: detects OS, picks the correct compose file, pulls images, and starts `isf-core` + `ai-proxy` containers. Prints dashboard URL on success.                           |
| `shutdown_isf_core.py` | One-command graceful shutdown: stops & removes all containers while preserving your `data/` directory.                                                                                    |
| `.env`                 | Infrastructure configuration (Tavily API key, Telegram, Git settings).                                                                                                                    |
| `.env.ai_proxy`        | **LLM provider keys only** (Gemini, DeepSeek, OpenAI) — isolated from the factory engine.                                                                                                 |
| `compose.yml`          | Standard Docker Compose orchestration file to spin up the container network on Linux/Windows hosts.                                                                                       |
| `compose.mac.yml`      | Tailored Docker Compose orchestration file optimized for MacOS volume and timezone mount paths.                                                                                           |

---

## ⌨️ Using the Platform

### ⌨️ UI Keyboard Shortcuts

| Shortcut                   | Scope           | Action                                                                                    |
| :------------------------- | :-------------- | :---------------------------------------------------------------------------------------- |
| **`Shift` + `Tab`**        | Chat Input      | **Toggle Dry Run:** Switches between Dry Run (Plan / Proposal) or Execute Mode.           |
| **`Alt` + `Enter`**        | Chat Input      | **AI Prompt Rephrase:** Automatically rephrases and optimizes your prompt before sending. |
| **`Ctrl / Cmd` + `Enter`** | Chat Input      | **Submit:** Instantly sends your prompt and attachments.                                  |
| **`Ctrl / Cmd` + `S`**     | File Editor     | **Save:** Saves your changes directly to the host workspace.                              |
| **`Tab`**                  | File Editor     | **Indent:** Inserts 2 spaces (`  `) at the cursor.                                        |
| **`Escape`**               | Modals & Panels | **Exit:** Closes the code editor, or exits fullscreen thinking logs.                      |

### 💬 Slash Commands (`/`)

Type `/` in the chat input to access a dropdown of native commands:

- **`/query <text>`** — Search local codebase.
- **`/web-search <query>`** — Search Google with AI summary.
- **`/deep-research <query>`** — Deep internet analysis.
- **`/run_codebase_testing`** — Run your unit test suites.
- **`/run_e2e_test @file`** — Run Playwright browser tests.
- **`/generate_unit_test @file`** — Write unit tests for a file.
- **`/fix-unit-test-file @file`** — Self-heal failing tests.
- **`/sonar-scan`** — Run SonarQube code quality scan.
- **`/sonar-issues [@file]`** — Fetch active code smells or bugs.
- **`/commit`** — Open the interactive git diff & commit modal.

### 💡 `@` Intellisense File Mentions

Mentions bring files directly into context:

1. Type `@` in the chat input.
2. Continue typing any part of a file path (e.g., `@app` or `@schema.sql`).
3. Press **`ArrowUp` / `ArrowDown`** and press **`Enter`** or **`Tab`** to select.
4. The system automatically formats your input as `@filename.py` to give the AI agent a direct file pointer.

---

## ⬆️ Scaling & Upgrading

ISF-Core starts with SQLite for zero-friction setup. As your usage grows, you can supercharge your factory engine by activating advanced AI tools and scaling parameters:

### Option 1: Migrate to Supabase (PostgreSQL)

If your database scales up, or you need enterprise Postgres features (such as pg_vector for embedding vector stores, pg_cron for database-level scheduling, and Row-Level Security), easily migrate your data layer.

👉 **[View Option 1 Setup Guide (Supabase Migration)](options_setup/option1_supabase.md)**

---

### Option 2: Add SonarQube for Automated Quality Gates

ISF integrates natively with SonarQube to provide continuous static code analysis and quality assurance on auto-pilot:

- **Scheduled Test Coverage Reports:** A cron job periodically triggers unit tests, generates coverage reports, and uploads them to SonarQube.
- **Auto-Remediation loops:** ISF reads code smells and security hotspot vulnerabilities directly from SonarQube APIs, refactors the source code to resolve the warning, and re-scans the repository to ensure quality gate compliance.

👉 **[View Option 2 Setup Guide (SonarQube Integration)](options_setup/option2_sonarqube.md)**

---

### Option 3: Connect to a Mobile Command Center (Telegram Integration)

Take your factory with you in your pocket. By configuring a private Telegram bot, you can securely interact with your AI workers from anywhere on your phone:

- **Direct Chat:** Task your agent, ask questions, or review design blueprints via chat.
- **Real-time Alerts:** Receive push notifications containing live agent progress, screenshots of browser runs, and reports when self-healing test loops complete.

👉 **[View Option 3 Setup Guide (Telegram Command Center)](options_setup/option3_telegram.md)**

---

### Option 4: Enable Real-Time Web Intelligence (Tavily Search Engine)

Standard LLMs are limited by knowledge cutoff dates. Integrating **Tavily** equips your agents with search engines optimized specifically for AI agent retrieval:

- **`/web-search` & `/deep-research`:** Run multi-step recursive search workflows.
- **Autonomous Documentation Ingestion:** Before writing code, agents can crawl live GitHub issues, StackOverflow threads, and official framework docs to ensure they use up-to-date, non-deprecated syntax.

👉 **[View Option 4 Setup Guide (Tavily Web Intelligence)](options_setup/option4_tavily.md)**

---

### Option 5: Deploy the Federated AI Database Agent (`db_agent`)

No more writing raw SQL to inspect your workspace data. Ask questions about system metrics or chat histories in plain, natural language:

- **Zero SQL Barrier:** Query chat histories or job logs in plain English.
- **Visual Vega-Lite Plots:** Automatically translates your data queries into rich, interactive dashboards.

👉 **[View Option 5 Setup Guide (Federated DB Agent)](options_setup/option5_db_agent.md)**

---

### Option 6: Enable Agentic Web Navigation (Browser Automation & Playwright)

Equip your agents with virtual "hands" to navigate the web. Using headless Chrome containers controlled via Playwright, your agents can perform browser-automation tasks:

- **Administrative Automation:** Automate complex actions like logging into portals (such as Summit, eLeave, or ITSM tools), retrieving leave balances, filing tickets, and approving workflow requests.
- **Interactive Snapshots:** The agent takes screenshots and tracks console logs at every stage, verifying DOM changes and self-healing when page layouts change.

👉 **[View Option 6 Setup Guide (Browser Automation Setup)](options_setup/option6_browser_automation.md)**

---

### Option 7: Automate Background Tasks (Cron-Scheduled Workflows)

Run your development department while you sleep. The built-in Cron Daemon lets you schedule routine engineering and admin workflows to execute periodically:

- Configure the system to trigger **"Morning Briefings"** (fetching calendar entries, compiling unread high-priority emails, and preparing task lists into a Markdown brief) or **"Weekly Code Sweeps"** (running SonarQube analysis and writing tests).
- **Direct Control:** Insert or update background jobs in the `cron_scheduled_jobs` database table easily through the Web Dashboard.

👉 **[View Option 7 Setup Guide (Cron Scheduling Workflow)](options_setup/option7_cron_workflows.md)**

---

## 🔧 Troubleshooting

| Problem                       | Solution                                                                                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Containers won't start**    | Run `docker compose ps` to check status. Ensure Docker Desktop is running. Check `docker compose logs isf-core` for errors.                    |
| **AI returns errors**         | Verify your API keys in `.env.ai_proxy` are valid and have sufficient credits. Check `docker compose logs ai-proxy` for authentication errors. |
| **Looping / stuck workflows** | ISF aborts after 3 retries if auto-fixes fail. Check the logs for `lint_errors` or test failures, or open a GitHub issue.                      |
| **Port conflict**             | If port 3006 or 8080 is already in use, edit `compose.yml` and change the host port (left side of the `ports:` mapping).                       |
| **Mac Docker issues**         | Use `compose.mac.yml` — it omits the `/etc/timezone` mount which is incompatible with macOS. `start_isf_core.py` handles this automatically.   |

---

## 💖 Support the Project & Feedback (Donations Welcome)

ISF-Core is a **free, self-hosted, independent** labor of love. There are no credit cards, no premium subscriptions, and no cloud-walled features. If this tool has saved you hours of debugging, streamlined your startup, or helped you coordinate complex applications, please consider supporting the project:

### 1. Support via Sponsorship & Donations

To help fund ongoing maintenance, hosting, automated test pipelines, and continuous development of our high-performance Nuitka core engine:

- **GitHub Sponsors:** [Become a backer on GitHub Sponsors](https://github.com/sponsors/agentic-river) to get a special supporter badge and join our private priority channel.
- **Ko-fi / Coffee:** [Buy us a coffee](https://ko-fi.com/isf-factory) to show your appreciation!

### 2. Help Us Build the Flywheel

- **Star the Repo ⭐:** Help us reach GitHub Trending! A simple star helps other builders discover ISF-Core.
- **Provide Feedback 💬:** Join our [GitHub Discussions](https://github.com/agentic-river/isf-core/discussions) and share your custom templates, system rules (`rules/`), or custom cron tasks.
- **Report Bugs 🐛:** Ran into an unexpected agent behavior or edge case? Open an issue on our [GitHub Issues](https://github.com/agentic-river/isf-core/issues).

---

## ⚖️ License

- The user workspace configuration elements (including `rules/`, `docs/`, and companion scripts) are licensed under the permissive **MIT License**.
- The pre-compiled factory engine binary is free to run, self-host, and scale for everyone under the **ISF-Core Free Use License**. No paywalls, no limits.
