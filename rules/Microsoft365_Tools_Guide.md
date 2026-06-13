# Microsoft 365 Tools Guide

## Objective
This document outlines the standard operating procedures and mandatory guidelines for AI agents when interacting with Microsoft 365 services (Email, Calendar, Tasks, Directory) via the Microsoft Graph API tools defined in `backend/core/m365_tools.py`.

## Actionable Directives

- **ALWAYS Resolve Names First:** When a user requests to schedule a meeting or send an email using only a first name or partial name, you MUST use `search_directory` to resolve the exact email address before calling `create_calendar_event` or `send_email`.
- **NEVER Send Emails Without Review (Unless Explicitly Authorized):** By default, when asked to reply to an email, you MUST use `create_draft_reply` rather than `send_email` so the human user can review the response in their Drafts folder. Only use `send_email` if the user explicitly says "send the email directly".
- **ALWAYS Verify Authentication (Non-Blocking & Self-Healing):** Authentication relies on MSAL. The system implements a robust, three-tiered authentication strategy:
  1. **True Silent Refresh (Self-Healing):** The system automatically utilizes the background Refresh Token (Master Key) to securely fetch new Access Tokens without user intervention.
  2. **Automatic 401 Recovery:** If a request fails with a 401 Unauthorized error due to a stale token, the central `_api_call` helper automatically bypasses the short-term cache (`force_refresh=True`) and retries the operation seamlessly.
  3. **Anti-Freeze Device Code Flow (Background Listener):** If manual re-authentication is strictly required (e.g., empty cache or expired master key), the system will initiate the Device Code Flow. It immediately raises a `PermissionError` containing the URL and user code (pushed to the UI) to halt the workflow and prevent the AI agent from freezing. Simultaneously, a **Background Thread** is spawned to silently poll Microsoft; once the user successfully authenticates in the browser, this thread securely writes the new token to `backend/data/token_cache.bin`.
- **Improved Reliability:** All M365 tools utilize a centralized `_api_call` helper that handles header injection, logging, and retry logic, minimizing silent failures and providing clearer diagnostic messages if the API remains unreachable.
- **Ensure Proper Scopes for Directory Search:** The `search_directory` tool requires access to the directory endpoints (e.g., `/me/people` or `/users`). Ensure that the `People.Read` and `User.ReadBasic.All` scopes are present in `backend/core/auth_msal.py`. If a persistent 403 Forbidden error occurs, verify these scopes and advise the user to delete their local token cache (`backend/data/token_cache.bin`) to trigger a new consent prompt.
- **ALWAYS Leverage Agentic Workflows First:** For complex requests like "process my inbox" or "what does my day look like?", you MUST prioritize the composite workflow tools (`perform_email_management_workflow`, `perform_morning_briefing_workflow`, `perform_inbox_triage_workflow`) over making multiple individual Graph API calls.
- **Handling System Approvals (e.g., RCS Claims):** When asked to approve a claim or system request (like RCS) from an email, you MUST extract the approval `mailto:` link or instructions from the email body. Then, use `create_draft_reply` (or equivalent Graph API logic) to generate the "Approved" email and place it in the user's Drafts folder. NEVER send the approval email directly without allowing the user to review the draft.

## Examples

### 🟢 Good Example
* **Good:** A user asks, "Set up a meeting with Bernard tomorrow." The agent first calls `search_directory(query="Bernard")` to get `bernard@company.com`, then calls `find_meeting_times(attendees=["bernard@company.com"])`, and finally calls `create_calendar_event(...)`.
* **Good:** A user asks, "Reply to Sarah saying I agree." The agent calls `create_draft_reply(message_id="...", reply_text="I agree.")` and informs the user the draft is ready for review.
* **Good:** A user asks, "Approve the RCS Claim." The agent parses the email for the approval `mailto:` link, extracts the destination and subject format, and creates a draft reply in the Drafts folder using `create_draft_reply`, informing the user that the approval draft is ready for their final click to send.

### 🔴 Bad Example
* **Bad:** Calling `send_email` automatically to reply to a sensitive client email without user confirmation.
* **Bad:** Attempting to call `create_calendar_event(attendees=["Bernard"])` without resolving the email address first, which will result in a Graph API error.
* **Bad:** Manually fetching unread emails, fetching the calendar, and fetching tasks separately when the user asks for a "morning briefing", instead of just calling `perform_morning_briefing_workflow()`.

## 4. Testing References

When modifying or extending M365 functionalities, ensure that you run the existing test suite to maintain expected behavior. The relevant unit test files are:

- `backend/tests/test_m365_briefing.py`: Specifically tests the empty/error state handling and correct unread email fetching in the morning briefing workflow.
- `backend/tests/test_m365_tools_all.py`: Contains comprehensive tests for all individual Microsoft Graph API tool functions and composite workflows in `m365_tools.py`, using mocked API responses.

### Test Execution:

pytest backend/tests/test_m365_briefing.py backend/tests/test_m365_tools_all.py
