# ⚡ FastAPI Async Proxy Protocol

This document defines the strict mandate for how backend route handlers must interact with the AI Proxy client to prevent event-loop blocking and frontend connection failures.

## 1. Objective

NEVER call a synchronous, blocking I/O function (e.g., `requests.post`) directly inside an `async def` FastAPI route. Doing so freezes the entire `asyncio` event loop for the duration of the network call, which starves all other concurrent requests—especially active Server-Sent Events (SSE) chat streams—causing frontend timeouts and "connection failure" errors.

## 2. The Golden Rule

**In any `async def` route handler, you MUST exclusively use the `_async` variants of the proxy client methods.**

| ✅ DO use in `async def` routes | 🔴 NEVER use in `async def` routes |
| :--- | :--- |
| `await client._post_to_proxy_async(...)` | `client._post_to_proxy(...)` |
| `await client.generate_content_async(...)` | `client.generate_content(...)` |
| `await client.stream_chat_async(...)` | `client.stream_chat(...)` |

## 3. Why This Matters

The proxy client (`backend/core/proxy_client/client.py`) exposes both synchronous methods (backed by `requests`) and asynchronous methods (backed by `httpx`). The synchronous methods block the Python thread they run on. When that thread is the main event-loop thread of FastAPI, **all** concurrent activity halts:

- Live SSE chat streams stop pushing chunks.
- Other API endpoints become unresponsive.
- The frontend hits its timeout and throws a connection error.

This failure mode is especially deceptive because:
- It only manifests with slower models (e.g., `deepseek-v4-pro` taking 10–30 s per call). Fast models like Gemini (1–2 s) mask the freeze.
- The proxy logs look normal (they show "no tools" or a valid route), making it appear to be a provider outage when it is actually a local event-loop stall.

## 4. Example

### 🔴 Bad — Blocks the event loop

```python
@router.post("/api/chat/auto_analyze_process")
async def auto_analyze_process(req: AnalyzeRequest):
    client = global_state.client
    # ⚠️ Synchronous requests.post() called inside async def — FREEZES EVERYTHING
    response = client._post_to_proxy("generate", payload)
    return {"result": response.json()}
```

### 🟢 Good — Cooperative async

```python
@router.post("/api/chat/auto_analyze_process")
async def auto_analyze_process(req: AnalyzeRequest):
    client = global_state.client
    # ✅ Uses httpx.AsyncClient under the hood — event loop stays alive
    response = await client._post_to_proxy_async("generate", payload)
    return {"result": response.json()}
```

## 5. Enforcement Checklist

Before merging any new or modified route handler, verify:

1. [ ] The handler is `async def` → all proxy calls use `await` + the `_async` method variant.
2. [ ] If the handler is `def` (synchronous), verify it runs on a threadpool or background task and does NOT share the main event-loop thread.
3. [ ] Manual QA: send a slow-model request (e.g., `deepseek-v4-pro`) while a chat stream is active. The stream MUST NOT stutter or drop.
