# 📚 Rules Index — Always-On Reference

This file is **always injected** into the AI's system instruction (before the top-5 query-matched rules). It serves as a discoverable directory: when the AI encounters a situation not covered by the injected rules, it MUST use `file_action(action="read", ...)` or `file_action(action="keyword_search", ...)` to look up the relevant rule from this index before proceeding.

**Maintenance:** When a rule is created, renamed, deleted, or significantly repurposed, `Rules_Index.md` MUST be updated accordingly. See `AI_Rule_Management.md` §5.

---

## 🧠 AI Behavior & Communication
| File | Summary |
|------|---------|
| `AI_Rule_Management.md` | Protocol for creating, modifying, and maintaining project rules |
| `Mermaid_Diagram_Protocol.md` | Mermaid diagram syntax, formatting, and anti-patterns |
| `Data_Visualization_Protocol.md` | Charts, data viz libraries, and formatting conventions |
| `Slash_Command_Creation_Guide.md` | How to add new `/commands` to the chat interface |
| `Inline_Image_Display_Protocol.md` | When to use `![]()` embeds vs browser tools for images |

## 🔧 Code Quality & Testing
| File | Summary |
|------|---------|
| `Python_Code_API_Guide.md` | Python conventions, type hints (§9), async patterns |
| `Test_Fixing_Protocol.md` | Test-driven autonomy: diagnosis, isolation, resolution, verification |
| `Sonar_Issue_Fixing_Protocol.md` | SonarQube issue resolution workflow |
| `Sonar_Security_Hotspot_Protocol.md` | Security hotspot handling in SonarQube |
| `React_Component_Guidelines.md` | React component standards, hooks, and patterns |
| `Recharts_Responsive_Guide.md` | Recharts `ResponsiveContainer` best practices for React 18+ |
| `UX_UI_Best_Practices_Guide.md` | UI/UX standards, layout, accessibility, and anti-patterns |

## 🛠️ Tool-Specific Guides
| File | Summary |
|------|---------|
| `Playwright_MCP_Usage_Guide.md` | Browser automation via Playwright MCP (navigate, click, snapshot) |
| `Playwright_E2E_Testing_Guide.md` | End-to-end testing with Playwright |
| `Agentic_Browser_Automation_V2_Guide.md` | V2 browser automation & routing protocol |
| `Github_MCP_Guide.md` | GitHub operations (PRs, issues, commits, search) |
| `Excel_Agent_Guide.md` | Excel document creation, reading, and manipulation |
| `Janus_Pro_MCP_Tools_Protocol.md` | Image generation via Janus-Pro MCP tools |
| `Context7_MCP_Docs_Guide.md` | Context7 documentation lookup service |
| `Microsoft365_Tools_Guide.md` | Microsoft 365 operations (email, calendar, tasks) |
| `ISF_Dev_UI_Visual_Inspection_Guide.md` | ISF-Dev UI visual inspection and enhancement |

## 🏗️ Infrastructure & Architecture
| File | Summary |
|------|---------|
| `Docker_Rebuild_Protocol.md` | When to rebuild containers after dependency changes |
| `FastAPI_Async_Proxy_Protocol.md` | Async proxy patterns to prevent event-loop blocking |
| `AI_Proxy_Calling_Protocol.md` | Canonical API contract for calling the AI Proxy |
| `AI_Proxy_File_Upload_Protocol.md` | File uploads through AI Proxy (Gemini File API) |
| `Cron_Service_and_Job_Scheduling_Spec.md` | Scheduled background task architecture and rules |
| `Supabase_PostgreSQL_Table_Creation_Guide.md` | Database table creation and migration protocol |
| `Bun_Nextjs_Management_Guide.md` | Bun & Next.js dependency and dev-server management |
| `Uv_Python_Package_Management_Guide.md` | UV Python package management conventions |
| `Tool_Registration_Discovery_Protocol.md` | How tools are registered, discovered, and routed |

## 🛡️ Safety & Compliance
| File | Summary |
|------|---------|
| `Workspace_Safety_Protocol.md` | Anti-destruction, git safety, concurrent session awareness |
