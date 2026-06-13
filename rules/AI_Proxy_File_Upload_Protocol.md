# 🤖 AI Proxy & Gemini File Upload Protocol

## 1. Objective
This document defines the strict architectural boundaries and workflow for handling file uploads (especially large documents like PDFs, PPTXs, CSVs) and communicating with the AI Proxy when using the Google Gemini File API.

## 2. Core Architectural Principle
**CRITICAL:** The main backend MUST remain completely ignorant of Gemini credentials. 
*   🔴 **NEVER** place the `GOOGLE_API_KEY` in the main backend's environment variables.
*   🔴 **NEVER** attempt to call `google.genai.Client()` directly from the main backend.
*   🟢 **ALWAYS** route file uploads and LLM generation requests through the isolated `ai_proxy` service.

## 3. Workflow Directives

### Phase 1: Uploading the File
When a user uploads a large file that requires native parsing by Gemini, follow this exact data flow to ensure the proxy handles the upload securely:

1.  **Frontend (`multipart/form-data`):** The frontend UI MUST post the raw file object to the main backend's upload endpoint (e.g., `POST /api/chat/upload`).
2.  **Main Backend (Streaming Passthrough):** The main backend MUST receive the file and immediately stream it directly to the AI proxy using `httpx.AsyncClient()`. It does not process or upload the file to Google itself.
3.  **AI Proxy (Native Gemini Upload):** The AI Proxy receives the file via its dedicated `/v1/upload` endpoint. It instantiates the `google.genai.Client()` using its isolated API key, uploads the file to Google's temporary 48-hour storage, and retrieves the `file_uri`.
4.  **Response Chain:** The proxy returns the `file_uri` to the main backend, which passes it back to the frontend to store in the chat state.

### Phase 2: Generating Content
When the user submits a chat message that includes an uploaded file:

1.  **Frontend Payload:** Instead of sending a massive Base64 inline string, the frontend MUST attach the lightweight `file_uri` and `mime_type` to the chat payload.
2.  **Main Backend:** The main backend attaches the URI data into the proxy generation request body.
3.  **AI Proxy (Context Generation):** The AI Proxy parses the incoming request, detects the URI, and safely constructs the Gemini context using `types.Part.from_uri(file_uri=..., mime_type=...)`.

## 4. Examples

### 🟢 Good Example: Main Backend Upload Passthrough
```python
# In main backend (routers/chat.py)
import httpx
from fastapi import APIRouter, UploadFile

@router.post("/api/chat/upload")
async def upload_file(file: UploadFile):
    # Stream directly to proxy to avoid holding key in main backend
    proxy_url = f"{os.getenv('PROXY_URL')}/v1/upload"
    async with httpx.AsyncClient() as client:
        files = {"file": (file.filename, file.file, file.content_type)}
        response = await client.post(proxy_url, files=files)
        return response.json() # Returns {"file_uri": "...", "mime_type": "..."}
```

### 🔴 Bad Example: Main Backend Calling Gemini Directly
```python
# In main backend (routers/chat.py)
from google import genai # ❌ BAD: Main backend shouldn't know about genai

@router.post("/api/chat/upload")
async def upload_file(file: UploadFile):
    # ❌ BAD: Assumes GOOGLE_API_KEY is in main backend
    client = genai.Client() 
    myfile = client.files.upload(file=file.file)
    return {"file_uri": myfile.uri}
```

## 5. Handling File Processing State (`FAILED_PRECONDITION`)
When uploading large media files (video, audio, heavy PDFs), Google places them into a `PROCESSING` state for indexing. If a prompt is triggered before indexing completes, Gemini throws a `400 FAILED_PRECONDITION` error.

*   🟢 **Mandatory Proxy Behavior:** The AI Proxy MUST gracefully catch this error in its generation endpoint. Instead of crashing or returning a 500 error to the user, the proxy MUST implement an asynchronous polling loop (e.g., wait 10 seconds and retry, up to a sensible timeout like 10 minutes) until the file state becomes `ACTIVE`.
*   🟢 **Live UI Progress Streaming:** During this waiting loop, the proxy MUST yield live JSON status updates (e.g., `{"status": "processing", "attempt": 1, "max_attempts": 120}`) through the Server-Sent Events (SSE) stream. The frontend UI MUST be configured to intercept these specific status chunks to update the user on the file's processing progress, rather than appending them as standard text.
*   🔴 **Incorrect Behavior:** Do not bubble the `FAILED_PRECONDITION` error back to the frontend, and do not expect the main Python backend to handle the retry logic. The proxy owns this entirely.

## 6. Gemini File Prompting Strategies (Best Practices)
When constructing the prompt arrays (whether in the proxy or system instructions), adhere to these official Google strategies to maximize multimodal reasoning success:

1.  **Order of Elements:** Always place the file/image part **first**, followed by the text instruction (e.g., `contents=[myfile, "Describe this audio clip"]`).
2.  **Step-by-Step Reasoning:** For complex documents or images (like math problems or multi-step logic), append instructions like *"Think step by step"* or explicitly outline the analytical steps.
3.  **Strict Output Formatting:** If a specific structure is required (like parsing a CSV or Table), strictly specify the format in the prompt (e.g., *"Parse the table in this image into markdown format"* or *"Provide the attributes in JSON format"*).
4.  **Troubleshooting Hooks:** If the LLM produces generic or hallucinated results, prepend instructions to explicitly analyze the file first: *"First, describe what's in the image/file in detail. Then, answer..."*