# Janus-Pro MCP Tools Protocol

## Objective
This document defines the mandatory protocol for AI agents using the **Janus-Pro MCP Tools** (`janus_pro_janus_image_to_text` and `janus_pro_janus_text_to_image`). These tools provide local multimodal capabilities (Vision + Image Generation) running on the Host's NVIDIA RTX 4090 GPU, bridging the visual gap for the DeepSeek LLM.

> **⚠️ IMPORTANT:** The MCPManager namespaces all tools by server name. The LLM sees `janus_pro_janus_image_to_text` and `janus_pro_janus_text_to_image`, NOT `janus_image_to_text` or `janus_text_to_image`.

## Infrastructure

| Component | Details |
| :--- | :--- |
| **Runtime** | Native (launched via `run_native_janus.sh` — NOT a Docker container) |
| **Port** | `8850` (SSE + REST) |
| **SSE Endpoint** | `http://127.0.0.1:8850/sse` (native) or `http://host.docker.internal:8850/sse` (from Docker containers) |
| **REST API (image-to-text)** | `POST http://127.0.0.1:8850/rest/janus_image_to_text` |
| **REST API (text-to-image)** | `POST http://127.0.0.1:8850/rest/janus_text_to_image` |
| **Health Check** | `GET http://127.0.0.1:8850/rest/health` |
| **Ping** | `GET http://127.0.0.1:8850/rest/ping` |

> **🚀 Performance Note:** The MCPManager routes all Janus-Pro tool calls via REST (not SSE/MCP) for speed. REST bypasses the SSE keepalive/heartbeat overhead and is ~1.6x faster. The REST endpoints are defined in `mcp-servers/janus-pro/server.py`.

## 1. Core Principles
- **Vision First:** When a user uploads an image or asks "What do you see?", you MUST route to `janus_pro_janus_image_to_text` — NEVER guess image contents from memory or filename.
- **Image Path Resolution:** You MUST provide an absolute path (e.g., `/app/data/tmp/upload.png`) or a valid base64-encoded string. Relative paths will fail because the server and the caller may run in different working directories.
- **Generated Image Display (Embedded Base64):** When `janus_pro_janus_text_to_image` returns a markdown string containing an embedded base64 data URI (e.g., `![filename](data:image/png;base64,iVBORw0KGgo...)`), you MUST render the markdown **as-is** in the chat response — do NOT strip, truncate, or modify the base64 string. The frontend Markdown renderer will automatically decode and display the image inline within the AI response bubble. If the tool returns a relative URL path instead (e.g., `/api/tmp/filename`), render it as a standard markdown image.
- **Lazy Loading Awareness:** The first tool call in a session may take 20-40 seconds due to lazy model loading (downloading + VRAM allocation). Subsequent calls are instant.
- **Never Hallucinate Visual Content:** If `janus_image_to_text` fails or returns an error, you MUST report the error to the user rather than fabricating a description.

## 2. Tool Reference

| Tool | Purpose | When to Use |
| :--- | :--- | :--- |
| `janus_pro_janus_image_to_text` | Analyze an image and answer a natural language prompt about it | User uploads an image, asks about visual content, requests OCR, asks "what is in this picture?" |
| `janus_pro_janus_text_to_image` | Generate an image from a text prompt | User asks to "create an image of...", "generate a picture of...", "draw..." |

## 3. Tool Signatures & Parameter Formats

### 3.1 `janus_pro_janus_image_to_text(image_path_or_base64: str, prompt: str) -> str`

**Parameters:**
- `image_path_or_base64` (string, REQUIRED):
  - **Absolute file path** on the container filesystem. E.g., `/app/data/tmp/upload_12345.png`
  - OR a **base64-encoded string** of the image bytes (for inline images).
  - OR a **URL** to an image (e.g., `http://isf-prod:8002/api/history/...`).
- `prompt` (string, REQUIRED): A natural language question or instruction about the image. Be specific. E.g., `"Describe this image in detail"`, `"What text is visible in this screenshot?"`, `"Is there a cat in this photo?"`

**Returns:** A text description from the Janus-Pro vision model.

**Example Call:**
```
janus_pro_janus_image_to_text("/app/data/tmp/screenshot.png", "What error message is shown on this screen?")
```

### 3.2 `janus_pro_janus_text_to_image(prompt: str, filename_prefix: str = "janus_img") -> str`

**Parameters:**
- `prompt` (string, REQUIRED): A detailed image generation prompt. More detail = better results. E.g., `"A golden retriever wearing a wizard hat, digital art, 4k"`.
- `filename_prefix` (string, optional): Prefix for the generated filename. Defaults to `"janus_img"`. Useful for organizing multiple generations.

**Returns:** A markdown image string. The tool may return one of two formats:
- **Embedded base64 data URI** (preferred): `![filename](data:image/png;base64,iVBORw0KGgo...)` — the image data is embedded directly in the markdown. Render this **as-is** in your chat response.
- **Relative URL path**: `![filename](/api/tmp/filename)` — render this as a standard markdown image.

> **🔴 CRITICAL:** Never truncate or summarize the base64 data URI. The full string may be very long (50,000+ characters). Include the complete markdown image tag in your response exactly as returned by the tool.

**Example Call:**
```
janus_pro_janus_text_to_image("A serene lake at sunset with mountains in the background, oil painting style")
```

## 4. Standard Workflows

### 4.1 Image Analysis Workflow
When a user uploads an image and asks about it:
1. **Identify the image path:** The uploaded file will be saved to the `TMP_DIR` (`/app/data/tmp/`). Extract the absolute path.
2. **Formulate a clear prompt:** Don't just pass the user's raw question — make it specific. E.g., user says "What's this?" → prompt should be `"Describe this image in detail, including all visible objects, text, and colors."`
3. **Call the tool:** `janus_pro_janus_image_to_text(image_path, prompt)`
4. **Present the result:** Display the model's description to the user in a clear, formatted way.

### 4.2 Image Generation Workflow
When a user asks to generate an image:
1. **Enhance the prompt:** If the user gives a vague prompt like "a cat", enhance it with style, quality, and composition details: `"A fluffy orange tabby cat sitting on a windowsill, soft morning light, photorealistic, 4k"`
2. **Call the tool:** `janus_pro_janus_text_to_image(enhanced_prompt)`
3. **Render the result:** The tool returns markdown — render it as-is in the chat so the user sees the image.

> **⏱️ Timeout Note:** Image generation takes ~90-100 seconds (REST timeout is 180s). Do NOT call the tool multiple times in parallel — the GPU can only handle one generation at a time. If the tool times out or fails with HTTP 400, check that Janus-Pro is running natively via `run_native_janus.sh` and the REST endpoint is reachable at `http://127.0.0.1:8850/rest/janus_text_to_image`.

## 5. Error Handling

| Error | Meaning | AI Agent Response |
| :--- | :--- | :--- |
| Model not loaded / timeout on first call | Lazy loading in progress (~20-40 seconds) | Inform user: "The vision model is loading into GPU memory. This takes ~30 seconds on first use. Please wait..." |
| `CUDA out of memory` | DeepSeek + Janus exceed 24 GB VRAM | Suggest: "The GPU is currently at capacity. Try closing other GPU-intensive tasks or reducing the model context size." |
| Empty or garbled response | Prompt was too vague or image quality was poor | Re-prompt with more specific instructions or ask user for a clearer image. |
| Connection refused / SSE error | Janus-Pro process is not running natively | Report: "The Janus-Pro vision server appears to be offline. Please run `run_native_janus.sh` to start it." |

## 6. Best Practices

### 🟢 Good
- **Be specific in prompts:** `"What error code is displayed in the red banner at the top?"` instead of `"What does this say?"`
- **Use absolute paths:** `/app/data/tmp/image.png` not `./image.png` or `tmp/image.png`
- **Enhance generation prompts:** Add style, quality, and composition keywords to `janus_text_to_image` prompts for better results.
- **Render markdown directly:** When the tool returns `![file](data:image/png;base64,...)` or `![file](/api/tmp/file)`, output it as-is in the chat message. The frontend MarkdownRenderer handles both formats.
- **Set meaningful `filename_prefix`:** Use descriptive prefixes like `"cat_wizard"` instead of the default `"janus_img"`.
- **Never truncate base64:** The base64 data URI may be extremely long. Do NOT shorten, compress, or replace it with a placeholder. Include the full, unmodified markdown tag.

### 🔴 Bad
- **Never** describe an image from memory or filename — always call `janus_image_to_text`.
- **Never** pass relative paths or assume the working directory.
- **Never** strip or modify the markdown image link returned by `janus_text_to_image`. This includes NEVER truncating base64 data URIs — include the full string.
- **Never** call both tools simultaneously if VRAM is tight — the model is shared and concurrent calls may OOM.
- **Never** use `janus_text_to_image` for text-based answers — it only generates images.
- **Never** replace the base64 data URI with a file path placeholder — the image must be rendered inline in the AI response bubble.

## 7. Model Constraints
- **Maximum Resolution:** Janus-Pro-7B processes images at 384x384 resolution internally. Very high-res images will be downscaled automatically.
- **Generation Resolution:** Image generation outputs at a fixed resolution determined by the VQ model. Do not request specific pixel dimensions — they will be ignored.
- **Single GPU:** Both inference and generation share the same RTX 4090. Concurrent tool calls are NOT recommended.
- **Auto-Detection:** The model auto-detects VRAM at startup. On GPUs with ≥16 GB VRAM (e.g., RTX 4090), it loads in native BF16 for maximum speed. On smaller GPUs, it falls back to 8-bit quantization to fit within limited VRAM.
