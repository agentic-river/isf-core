# 🗺️ ISF-Core UI Tour Guide

Welcome to the ISF-Core interface! Once you have the application up and running at `http://localhost:3006`, here is a guided walkthrough of the essential features to familiarize yourself with the dashboard and verify your AI connections.

## 1. 🟢 System Health Indicator (Top-Right Corner)

Look for the **"System Healthy"** badge with a pulsing green dot in the top-right header. Click it to open the **System Health UI** panel.

![System Health Dashboard](data:image/png;base64,IMAGE_DATA_UNAVAILABLE)

This image displays the **Infrastructure Status Dashboard**. You can see the real-time health of various core infrastructure components, including backend services, AI LLM providers, and MCP servers. Key indicators like Core Health, MCP Servers, Warnings, and Critical Errors are prominently displayed at the top. Below, individual service cards show their enablement status and health index.

- **Purpose:** Real-time status of all connected services — backend API, AI proxy gateways, MCP servers, and optional integrations (Supabase, Playwright, Tavily, Telegram).
- **Important Check:** Confirm your **AI LLM** provider (configured in `.env.ai_proxy`) shows **healthy**. A green status means the proxy can reach your chosen provider and your API key is valid.
- Also reachable via the hamburger menu → **System Health Status**, or by clicking the tab bar → **System Health**.

## 2. 📂 Resizable Sidebar — Chat History & Project Explorer

The left sidebar is your command center, split into two collapsible accordion sections:

**Chat History (top section):**

- **"New Chat" button** — Starts a fresh AI conversation thread.
- **Status Filter Pills** — Filter conversations by status: All, WIP (in-progress), Unread, KIV (pinned), Trash, or Archived. Count badges show real totals.
- **Tag Filter Pills** — Toggle with the tag icon to filter by custom tags you've assigned to threads.
- **Deep Search** — Type in the search bar and press **Enter** for a Google-style full-text search across all chat history (server-side). On-the-fly typing does a local title/tag match.
- **Date Grouping** — Threads are automatically grouped into Today, Yesterday, This Week, and Older.
- **Bulk Select Mode** — Click the checkbox icon to enter select mode. Tick multiple sessions, then batch-apply Read, Pin, Archive, or Trash.
- **Trash Management** — When viewing the Trash filter, an "Empty Trash" button permanently deletes all trashed items.

**Project Explorer (bottom section):**

- **Git-Aware File Tree** — Expand folders and click any file to load it in the built-in editor. Modified files (dirty git status) are visually highlighted.
- **Filter Files** — Search by filename to quickly navigate large projects.
- **Git Branch Toggle** — Click the branch icon to show **only modified files**. A red badge displays the count of dirty files.
- **Expand/Collapse All** — Use the chevron icons to expand or collapse every folder in the tree at once.

> 💡 **Pro Tip:** Single-click a file to insert `@filename` into the chat input. Double-click to open it directly in the built-in code editor.

## 3. 💬 Chat Input — Slash Commands, @Mentions & Power Tools

The chat input bar at the bottom of the screen is your primary interface for communicating with the AI. It's loaded with interactive features:

### ⌨️ Keyboard Shortcuts

| Shortcut             | Action                                          |
| -------------------- | ----------------------------------------------- |
| `Ctrl/Cmd + Enter`   | Send message immediately                        |
| `Alt/Option + Enter` | AI-powered prompt rephrase before sending       |
| `Shift + Tab`        | Toggle Dry Run / Execute Mode                   |
| `Escape`             | Dismiss suggestion dropdown or cancel edit mode |

### 🔍 Slash Commands (`/`)

Type `/` at any point in your message to trigger an **autocomplete dropdown** of available commands. Use `ArrowUp`/`ArrowDown` to navigate and `Enter` or `Tab` to select:

- `/query` — General-purpose AI query
- `/web-search` — Search the web and synthesize results
- `/deep-research` — Multi-step deep research workflow
- `/run_codebase_testing` — Run backend test suites
- `/run_e2e_test` — Run Playwright end-to-end tests
- `/generate_unit_test` — Auto-generate unit tests for a file
- `/fix-unit-test-file` — Repair a failing test file
- `/sonar-scan` — Trigger SonarQube static analysis
- `/sonar-issues` — View SonarQube issues by severity
- `/commit` — Git commit with auto-generated message

### 📎 @ File Mentions

Type `@` followed by any part of a filename to see a **context-aware dropdown** of matching project files. Navigate with `ArrowUp`/`ArrowDown` and select with `Enter` or `Tab`. The system inserts `@filename.py` (with a trailing space) so the AI knows exactly which file you're referencing.

### 📁 File Attachments & Image Paste

- **"Attach File" Button** — Click the paperclip icon to upload files (PDF, Excel, Word, CSV, JSON, images, videos — up to 200MB). Uploaded files appear as thumbnail chips above the input.
- **Image Paste** — Paste an image from your clipboard (`Ctrl/Cmd + V`) directly into the chat. The image is automatically converted to base64 and attached.
- **Remove Attachments** — Click the `×` button on any attachment chip to remove it before sending.

### 🧪 Dry Run Toggle

A **slider toggle** (or `Shift + Tab`) switches between:

- **Execute Mode** (default) — The AI writes changes directly to your workspace files.
- **Dry Run** — The AI only _plans and proposes_ changes without modifying any files.

The current mode is displayed as a small toggle switch next to the input area.

### 🤖 Runtime Model Selector

Use the **model dropdown** next to the input to swap LLM providers and models **on the fly** without restarting the application. Available models are listed with their provider name (e.g., `openai/gpt-4o`, `anthropic/claude-sonnet-4-20250514`).

### ✨ AI Prompt Rephrase (`Alt + Enter`)

Press `Alt + Enter` (or click the **Rephrase** button with the magic wand icon) to have the AI automatically optimize your draft prompt. The rephrased version is appended below a separator line, preserving your original wording for reference.

### 🔄 Session Controls

Below the text area, a toolbar provides session management:

- **New Chat** (`+`) — Starts a fresh conversation thread (clears all history).
- **Clone** (branch icon) — Clones the current session into a new branch, preserving message history up to the clone point. Only visible when messages exist.
- **Scroll to Top / Bottom** — Quick navigation buttons. The Bottom button shows a **lock icon** when auto-scroll is engaged (locked to follow streaming output).
- **Collapse / Expand All** — Toggles between showing all messages and collapsing AI responses to show only user messages.
- **Stop Generation** — When the AI is actively generating, the Send button turns into a red pulsing **Stop** button. Click to abort the current generation. If you type a new message while the AI is running, the Send button turns orange — sending will interrupt and inject your new message as **steering advice**.

### ✏️ Edit Mode

Hover over any user message and click the **pencil icon** to enter edit mode. The message bubble transforms into a full ChatInput, giving you access to all features (slash commands, @mentions, file attachments, Dry Run toggle, Rephrase) while editing. From edit mode you can:

- **Save** — Overwrite the message and all subsequent AI responses are re-generated.
- **New Session** — Branch off a new session from the edited message.
- **Cancel** — Discard changes.

## 4. 💬 Message List — Conversation Display & Interaction

The message list is the central area where your conversation with the AI unfolds. It uses **virtualized rendering** for smooth performance with large conversations and is packed with interactive features:

### 🧱 Message Layout

Each message is displayed as a card (bubble) with a consistent structure:

- **User messages** — Right-aligned with a blue user avatar, displayed in a bordered surface card.
- **AI messages** — Left-aligned with a Bot avatar, with expandable Thinking Process panel above when tool calls are present.
- **Timestamp** — Date and time displayed below each bubble.
- **Token Usage Bar** — Below each AI response, a compact bar shows: model name, run mode (Plan or Execute), input tokens (↓), output tokens (↑), estimated cost ($), and KV cache hit/miss counts (DeepSeek).

### 🎮 Hover Actions

Hover over any message to reveal action buttons:

| Icon           | Action                                          | Availability  |
| -------------- | ----------------------------------------------- | ------------- |
| 🔄 (RefreshCw) | Re-run — resend this exact message to the AI    | User messages |
| ✏️ (Pencil)    | Edit — enter edit mode with full ChatInput      | User messages |
| 🗑️ (Trash2)    | Delete — remove the message (with confirmation) | All messages  |

### 📎 Image Attachments

Images attached by the user or generated by the AI are rendered inline as **downloadable thumbnails** with a max height of 256px. Click to view full-size.

### 📄 Document Attachments

Non-image file attachments appear as styled cards with a file icon, filename, and "Document Attachment" label.

### 🎯 Search Highlight

When a full-text search match is found (triggered from the sidebar Chat History deep search), matching messages are **highlighted with a blue ring** and the view auto-scrolls to center the match.

### 📦 Collapse/Expand System

Two modes control how AI responses are displayed:

1. **Group Expand/Collapse** — When "Collapse All" is active, AI responses are hidden behind each user message. A **"Show response"** chevron button appears on the right of user messages. Click to expand just that group, revealing the AI's reply. Click **"Hide response"** to collapse it again.

2. **Collapse All / Expand All Toggle** — A pill toggle bar at the top of the message list (with Minimize2/Maximize2 icons) globally switches between showing all messages or hiding all AI responses.

### 🧠 Suggested Next Steps (Agent Actions)

After the AI completes a task, a row of **"Suggested Next Steps"** buttons appears below the last AI response. Each shows a label and reasoning, letting you continue the workflow with one click.

### 🔄 Auto-Scroll Behavior

- **Streaming** — The view auto-scrolls to follow the AI's live output.
- **User interrupt** — If you manually scroll up (mouse wheel or touch), auto-scroll **immediately disengages**. The Bottom button shows an unlocked arrow icon.
- **Re-engage** — Click the **Bottom** button to re-engage auto-scroll (lock icon appears).
- **Session switch** — Auto-scroll resets and scrolls to the bottom on session change.

### ⏳ Agentic Wait Panel

When the AI is in an **agentic loop** (performing multiple tool calls), a wait panel appears at the bottom of the last AI message showing remaining wait time, with a button to send a follow-up message.

### 🚦 Preflight Status

Before executing file modifications, the AI runs a **Preflight check**. Results (checks, warnings, errors) are rendered inline below the AI response bubble with color-coded indicators.

## 5. 🧠 Thinking Process Dashboard

Every AI response includes an expandable **Thinking Process** panel that traces the agent's reasoning step by step:

- **Color-Coded Tool Cards:**
  - 🟣 **Purple** — Internal reasoning / chain-of-thought
  - 🟡 **Yellow** — Progress updates (`report_progress`)
  - 🔵 **Blue** — Steering injections from the user
  - 🟢 **Green** — Successfully executed tools
  - 🔴 **Red** — Errors / tool execution failures
- **Progress Bar** — For multi-step tasks, a blue progress bar at the top shows completion percentage.
- **Duration Timer** — A live elapsed-time counter tracks how long the agent has been working.
- **Full-Screen Mode** — Click the maximize icon to expand the panel into a full-screen overlay (press `Escape` to exit).
- **Stop Agent Button** — A red "Stop Agent" button lets you abort a runaway or stuck generation.
- **Auto-Scroll** — The panel auto-scrolls to the latest tool call. Scroll up to detach and inspect earlier steps; a "scroll to bottom" button re-engages auto-follow.

## 6. 📑 Multi-Tab Workspace

The tab bar below the header lets you switch between AI chat and specialized dashboards without losing context:

| Tab                | Description                                                                |
| ------------------ | -------------------------------------------------------------------------- |
| **Chat**           | Primary AI conversation interface (default view)                           |
| **Browser Agent**  | Manage headless browser automation tasks (Playwright)                      |
| **DB Agent Admin** | Configure federated database connections and schemas                       |
| **Agentic BI**     | Create and view natural-language-powered data widgets                      |
| **Rule Health**    | Inspect and manage the AI's self-written operational rules                 |
| **Token Usage**    | Real-time charts of token consumption, micro-costs, and provider breakdown |
| **Admin Console**  | System administration, Docker management, and global settings              |
| **System Health**  | Live service connectivity dashboard                                        |
| **AI Manager**     | Queue of pending AI worker wishes and task delegation                      |
| **Cron Dashboard** | Scheduled background job management (create, edit, view history)           |
| **File Editor**    | Built-in syntax-highlighted editor for any file opened from the sidebar    |

> 💡 File editor tabs show an orange dot and italic filename when the file has unsaved modifications. Press **`Ctrl/Cmd + S`** to save directly to disk.

## 7. 📊 Status Bar & Token Cost Tracker

The status bar at the bottom of the header area provides at-a-glance operational metrics:

- **MTD Cost** — Month-to-date estimated spend across all LLM providers.
- **Message Count** — Number of messages in the current chat session.
- **Reindex** — Manually triggers a re-index of the workspace file tree and git status. Shows a progress indicator while scanning.
- **Token Usage** — Click to open the full Token Usage dashboard with daily input/output charts.
- **Memory** — Opens the memory inspector modal to view or clear the current session's message history.

## 8. 🔼 App Header & Hamburger Menu

- **Sidebar Toggle** (`PanelLeft` icon) — Show or hide the left sidebar.
- **Hamburger Menu** — Quick access to all dashboards (Browser Agent, Admin Console, System Health, AI Manager, Cron Services, DB Agent Admin, BI Dashboard, Rule Health) plus **Preferences** — see [Section 9](#9--preferences--design-system) for the full settings walkthrough.
- **Commit Button** — Appears active (blue) when there are uncommitted git changes. Opens the interactive git diff & commit modal.

## 9. 🎨 Preferences & Design System

Click **Preferences** from the hamburger menu (or the gear icon in the header) to open the **Preferences & Design System** modal. This is your personalization hub — all settings are persisted to `localStorage` instantly, with a live theme preview on the right.

### 🌓 Appearance — Mode Toggle

A three-button segmented control at the top lets you switch color schemes:

| Button | Icon | Behavior |
|--------|------|----------|
| **System** | 🖥️ `Monitor` | Follows your OS-level dark/light preference. Listens for real-time OS theme changes and updates the UI automatically. |
| **Light** | ☀️ `Sun` | Forces light mode across all components, code blocks, and Mermaid diagrams. |
| **Dark** | 🌙 `Moon` | Forces dark mode — the default for most developers. Mermaid charts and syntax highlighting switch to dark-optimized palettes. |

> 💡 The active mode is applied immediately to `<html data-theme>`. Markdown rendering, Mermaid diagrams, and syntax-highlighted code blocks all resolve their internal themes from this setting.

### 🎨 Color Theme — 6 Accent Swatches

Six circular color buttons let you change the primary accent used across buttons, links, active tabs, and the System Health indicator:

| Swatch | CSS Token | Vibe |
|--------|-----------|------|
| **Modern Indigo** `#4f46e5` | Default | Clean, professional blue-purple |
| **GitHub Green** `#2da44e` | `green` | Familiar GitHub-inspired green |
| **Ocean Blue** `#0969da` | `blue` | Calm, corporate blue |
| **Royal Purple** `#8250df` | `purple` | Rich, creative purple |
| **Sunset Orange** `#bc4c00` | `orange` | Warm, high-contrast orange |
| **River ISF (Logo Theme)** `#0050f0` | `river` | Brand-aligned ISF-Core signature blue |

The active swatch shows a white checkmark and a ring highlight. The **Theme Preview** panel on the right updates in real time — showing Primary, Secondary, Tertiary, and Neutral color chips with gradient bars so you can see the full tonal range before committing.

### 🔤 Typography — Font & Size

Two dropdowns control the reading experience across the entire UI:

- **Font Family:**
  - **Sans Serif (Inter)** — Clean, modern, high legibility. Default.
  - **Serif (Georgia)** — Classic, editorial feel. Great for long-form reading.
  - **Monospace (JetBrains Mono)** — Developer-centric fixed-width font. Ideal for code-heavy workflows.
- **Font Size:**
  - **Small (14px)** — Compact, fits more content on screen.
  - **Medium (16px)** — Balanced default. Browser-standard body size.
  - **Large (18px)** — Accessible, relaxed reading for presentations or reduced eye strain.

The right panel's typography preview shows a large "Aa" headline and the pangram *"The quick brown fox jumps over the lazy dog"* in the selected font, so you can evaluate readability before closing the modal.

### 🤖 AI Intelligence — Primary Chat Model

The bottom-left section lets you choose which LLM powers your conversations:

- **Primary Chat Model dropdown** — Lists all models loaded from your AI proxy configuration (e.g., `openai/gpt-4o`, `anthropic/claude-sonnet-4-20250514`). Each entry shows its provider key and model ID.
- **Reload button** (`RefreshCw` icon) — Triggers a backend reload of the model registry (`POST /api/system/models/reload`), picks up any `.env.ai_proxy` changes without restarting the container.
- A spinning loader indicates model fetching is in progress.
- The selected model is persisted and used as the default in the chat input's model selector.

### 🖼️ Theme Preview Panel (Right Side)

The right half of the modal is a live sandbox that reacts to every change:

1. **Color System** — Four cards (Primary, Secondary, Tertiary, Neutral), each with a 5-stop gradient bar showing the full lightness scale used by Tailwind utilities.
2. **Typography** — "Aa" headline + body text rendered in the active font family. A tag in the corner shows the current font name.
3. **UI Components** — Real rendered buttons: Primary filled, Secondary filled, Inverted (text-on-bg), and Outlined border button. These use the active color theme so you can judge contrast and hover states.

> 💡 All settings are saved to your browser's `localStorage` under the `app-settings` key. The **Save Preferences** button at the bottom simply closes the modal — changes take effect immediately as you interact with the controls.
