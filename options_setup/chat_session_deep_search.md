# 🔍 Chat Session Deep Search Guide

This guide explains how to use the **Deep Search** feature in the ISF-Core Chat History sidebar to perform Google-style full-text searches across your entire chat history — including message contents, session titles, and tags.

## Why Use Deep Search?

- **Find Anything Instantly:** Search across all messages and sessions, not just the 50 most recent ones loaded in the sidebar.
- **Advanced Query Operators:** Use Google-style syntax (`"exact phrase"`, `-exclude`, `wildcard*`, `OR`, grouping) for precise filtering.
- **Server-Side Pagination:** Results are fetched from the backend in pages of 50, with a "Load More" button to continue scanning deeper history.
- **In-Message Highlighting:** Clicking a deep search result highlights matching terms inside the conversation view so you can jump directly to the relevant context.

---

## 1. Two Search Modes

The sidebar search bar supports two distinct search behaviors, triggered differently:

| Mode | Trigger | Behavior |
|:---|:---|:---|
| **Client-Side Filter (Local)** | Typing (keystroke) | Filters the already-loaded 50 sessions by matching title and tag text. Instant, no server request. |
| **Deep Search (Server-Side)** | Pressing **Enter** | Sends a full-text search query to the backend, scanning all messages and sessions across the entire database. Results replace the normal chat list. |

> 💡 **Tip:** Use local filtering for quick navigation by title or tag. Use Deep Search (Enter) when you need to find a specific message buried deep in your history.

---

## 2. Deep Search Query Operators

The deep search query parser (`searchQueryParser.js`) supports the following Google-style operators. You can combine them freely in a single query.

### A. Literal Terms

Plain words are matched as substrings against message content, titles, and tags.

```
deployment error
```

Finds any session containing both `deployment` AND `error` (AND semantics by default).

### B. Exact Phrases

Wrap text in double quotes to match the exact phrase.

```
"docker compose up"
```

Only matches content containing the literal phrase `docker compose up`.

### C. Exclusions (Negative Match)

Prefix a term with `-` to exclude sessions containing that term.

```
database -sqlite
```

Finds sessions mentioning `database` but NOT `sqlite`.

Exclusions also work with quoted phrases and wildcards:

```
api -"deprecated endpoint" -*.test
```

### D. Wildcards

Use `*` to match any sequence of characters.

```
debug*
```

Matches `debug`, `debugging`, `debugger`, `debug-tool`, etc.

> ⚠️ Wildcard patterns are converted to regular expressions internally. If the converted regex is invalid, the parser falls back to a simple substring match (stripping `*` characters).

### E. OR Groups

Use `OR` or `|` to match sessions containing at least one of the alternatives.

```
react OR vue OR angular
```

Equivalent to:

```
react | vue | angular
```

### F. Parenthetical Grouping

Use `(...)` to group terms into a logical unit. Each parenthetical group acts as an OR group internally.

```
(frontend bug) production
```

This parses as: match sessions that contain EITHER `frontend` OR `bug`, AND also contain `production`.

You can nest exclusions inside groups:

```
(login -password) dashboard
```

---

## 3. How Deep Search Works (Architecture)

```
User presses Enter in sidebar
        │
        ▼
ResizableSidebar.jsx ── GET /api/history/search?q=...&limit=50&offset=0 ──► backend/routers/chat_history.py
        │                                                                        │
        │  deepSearchResults state updated                                       ▼
        │                                                                 db.search_messages(q, limit, offset)
        │                                                                        │
        │                                                                        ▼
        │                                                          _search_messages_supabase() / _search_messages_sqlite()
        │                                                                        │
        │                                             ┌──────────────────────────┼──────────────────────────┐
        │                                             │                          │                          │
        │                                             ▼                          ▼                          ▼
        │                                 messages content search      sessions title/tags search      exclude filters
        │                                 (paginated, ordered desc)     (paginated)                    (paginated)
        │                                             │                          │                          │
        │                                             └──────────────────────────┼──────────────────────────┘
        │                                                                        ▼
        │                                                       results: Dict[session_id, match_count]
        │                                                                        │
        │                                                             sorted by match_count desc
        │                                                             sliced by offset:offset+limit
        │                                                                        │
        │                                                                        ▼
        │                                                       db.get_sessions_by_ids(session_ids)
        │                                                         → full session metadata
        │                                                                        │
        │◄────────── enriched session objects with match_count ─────────────────┘
        │
        ▼
deepSearchResults rendered in sidebar (replaces normal chat history)
        │
        ▼
User clicks a session → chat_search_match CustomEvent dispatched
        │
        ▼
MessageList.jsx receives event → highlightQuery state set
        │
        ▼
Matching terms highlighted in the conversation messages
```

### Backend Pagination (PostgREST 1000-Row Limit)

Supabase's PostgREST API enforces a **1000-row maximum** per request. The backend handles this transparently by looping with `.range(offset, offset + 999)` until all matching rows are scanned. Results are then sorted by `match_count DESC`, and the requested `limit`/`offset` slice is returned.

### Search Ordering

- Messages are searched by `id DESC` so **newest messages are searched first**.
- Final results are returned sorted by **`match_count` descending** (sessions with the most keyword hits appear first).
- Secondary ordering follows `updated_at DESC` from the session metadata.

---

## 4. Frontend Pagination ("Load More")

Deep search results are **independent paginated lists**, not overlaid on the normal chat history. Two separate "Load More" buttons exist in the sidebar:

| Context | Condition | Action |
|:---|:---|:---|
| **Normal History** | `hasMore && !chatSearchTerm.trim()` | Fetches next 50 sessions from `/api/history/sessions` |
| **Deep Search** | `deepSearchHasMore && chatSearchTerm.trim()` | Fetches next 50 matches from `/api/history/search?offset=N` |

### Key State Variables

| State | Purpose |
|:---|:---|
| `deepSearchResults` | Full session objects returned by the backend (enriched with `match_count`) |
| `deepSearchOffset` | Current offset for the next "Load More" fetch |
| `deepSearchHasMore` | Whether the last fetch returned a full page (≥ 50 results) |
| `isSearchingDeep` | Loading spinner state during fetch |

---

## 5. Message Highlighting in Conversation View

When you click a deep search result session:

1. `ResizableSidebar.jsx` dispatches a `chat_search_match` CustomEvent with the search query.
2. `MessageList.jsx` listens for this event and sets `highlightQuery` state.
3. Messages containing the query text are visually highlighted in the conversation area.

If a new message is loading (streaming), the highlight is cleared automatically to avoid stale context.

---

## 6. Key Source Files

| Layer | File | Role |
|:---|:---|:---|
| Frontend Parser | `frontend/src/components/sidebar/searchQueryParser.js` | Google-style query tokenizer and matcher |
| Frontend Sidebar | `frontend/src/components/sidebar/ResizableSidebar.jsx` | `performDeepSearch()`, state management, "Load More" |
| Frontend Messages | `frontend/src/components/chat/MessageList.jsx` | `chat_search_match` event listener, term highlighting |
| Backend Router | `backend/routers/chat_history.py` | `GET /api/history/search` endpoint |
| Database Layer | `backend/core/chat_storage/chat_storage.py` | `search_messages()`, `get_sessions_by_ids()` |
| Architecture Docs | `docs/chat_persistence_architecture.md` §26 | Full technical specification |
