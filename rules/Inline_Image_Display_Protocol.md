# 🖼️ Inline Image Display Protocol

<!-- TRIGGER_KEYWORDS: picture, image, photo, pic, cat, dog, meme, show me, wallpaper, screenshot of, get me a, find me a, cute, funny pic, funny picture -->

## Objective
When a user asks to see an image or picture, the AI MUST deliver the image **inline** inside the chat bubble using Markdown image syntax — NOT by giving the user a link to click. The chat's Markdown renderer natively supports `![alt](url)` and will render the image directly in the response.

## 1. Decision Tree

```
User asks for a picture/image?
  ├─ Is there a UI interaction required? (e.g., "log in and screenshot the dashboard")
  │   ├─ YES → Use Playwright/browser as normal.
  │   └─ NO  → Do NOT use Playwright. Follow the "Static Image" path below.
  │
   └─ Static Image path:
       1. Search for a **direct image URL** (ending in .jpg, .png, .gif, .webp, etc.)
          - Use perform_web_search_workflow to find image sources.
          - Query image APIs (e.g., thecatapi.com, pexels.com, picsum.photos).
          - Use fetch_page_content for API JSON responses that return image URLs.
       2. Extract the direct .jpg/.png/.gif/.webp URL.
       3. **Verify the URL resolves** using fetch_page_content before embedding.
          - If blocked or errored, try the next candidate source.
       4. Embed with: ![description](DIRECT_IMAGE_URL)
```

## 2. Core Directives

- **ALWAYS embed images inline:** Use Markdown `![description](DIRECT_IMAGE_URL)` syntax.
- **NEVER share a page URL as a substitute for an image:** Telling the user "go to https://cataas.com/cat" is NOT acceptable when they asked to see a picture. The image must appear inside the AI response bubble.
- **Playwright is for UI interaction, not image delivery:** Unless the user explicitly asks to navigate, click, log in, or interact with a web portal, the browser tools are the wrong tool for fetching static images.
- **Prefer image APIs over scraping HTML pages:** APIs like `https://api.thecatapi.com/v1/images/search`, `https://picsum.photos/800/400`, or Pexels direct URLs (`https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg`) return direct image URLs. Use these whenever possible.
- ⚠️ **Unsplash anti-bot warning:** `source.unsplash.com` and `unsplash.com` frequently block automated requests via anti-bot protection. Use **Pexels** as a more reliable fallback for general stock photography. Do NOT keep retrying Unsplash if it returns an error.
- **ALWAYS verify image URLs before embedding:** Call `fetch_page_content(url)` on every candidate image URL before embedding it in a Markdown `![]()`. If the URL returns an error or is blocked, discard it and move to the next candidate source. Never embed an unverified URL.
- **Fallback — extract <img> src if browser is unavoidable:** If the only available image is on an HTML page, use `fetch_page_content` to read the HTML, extract the `<img src="...">` attribute, and embed that direct URL — NOT the page URL.

## 3. Examples

### 🟢 Good Examples

- **User:** "get me a cute cat pic"
  **AI:** Calls `perform_web_search_workflow("cute cat picture API")` → discovers thecatapi.com →
  Calls `fetch_page_content("https://api.thecatapi.com/v1/images/search")` → extracts `url` field →
  Responds: `![Cute Cat](https://cdn2.thecatapi.com/images/abc123.jpg)`
  ✅ Image renders inline in the chat bubble.

- **User:** "show me a random landscape photo"
   **AI:** Constructs a direct Picsum URL →
   Responds: `![Landscape](https://picsum.photos/800/400)`
   ✅ Image renders inline.

- **User:** "show me a beautiful house by a lake and mountain"
   **AI:** Calls `perform_web_search_workflow("beautiful house lake mountain pexels")` →
   Extracts photo IDs from search results →
   Builds direct URL: `https://images.pexels.com/photos/18720930/pexels-photo-18720930.jpeg?auto=compress&cs=tinysrgb&w=1200` →
   Calls `fetch_page_content(url)` to verify it loads successfully →
   Responds: `![Lake House](https://images.pexels.com/photos/18720930/pexels-photo-18720930.jpeg?auto=compress&cs=tinysrgb&w=1200)`
   ✅ Image renders inline, URL verified before embedding.

- **User:** "find me a funny dog meme"
  **AI:** Calls `perform_web_search_workflow("funny dog meme")` → finds an image result URL →
  Verifies URL ends in `.jpg`/`.png`/`.webp` →
  Responds: `![Funny Dog Meme](https://example.com/dog-meme.jpg)`
  ✅ Image renders inline.

### 🔴 Bad Examples

- **User:** "get me a cute cat pic"
  **AI:** Calls `browser_action("navigate", "https://cataas.com/cat")` → `browser_take_screenshot()`
  → Responds: "Go to https://cataas.com/cat to see it"
  ❌ User gets a text link instead of an inline image.

- **User:** "show me a photo of a sunset"
  **AI:** Returns: "Check out this sunset: https://example.com/sunset.html"
  ❌ User must click away from the chat to see the image.

- **User:** "can you get a cute puppy picture?"
  **AI:** Uses Playwright to screenshot a Google Images search results page.
  ❌ Massive over-engineering for a simple static image request. Use `perform_web_search_workflow` + `fetch_page_content` instead.

## 4. Fallback Strategy

When a source fails, follow this ordered approach:

1. **Primary attempt:** Use a known reliable image API (Pexels, Picsum, thecatapi).
2. **If blocked/errored:** Immediately switch to the next source in the priority list. Do NOT retry the blocked source more than once.
3. **Priority order for stock photography:**
   - **Pexels** (`images.pexels.com`) — most reliable for general stock photos.
   - **Picsum** (`picsum.photos`) — reliable for placeholder/random landscapes.
   - **Unsplash** (`source.unsplash.com`) — high quality but often blocked by anti-bot; use only as last resort.
4. **If all direct image APIs fail:** Use `perform_web_search_workflow` to find an image on a CDN or news site, extract the direct URL, verify it, and embed.

```
Source Failed?
  ├─ Pexels → Try Picsum
  ├─ Picsum → Try Unsplash
  ├─ Unsplash → Use perform_web_search_workflow for a CDN-hosted image
  └─ All failed → Inform the user that all image sources are currently unavailable
```

### 🔴 Bad Fallback Example

- **User:** "show me a mountain lake house"
  **AI:** Calls Unsplash → blocked. Calls Unsplash again → blocked. Calls Unsplash a third time → blocked.
  ❌ Wastes iterations retrying a known-blocked source. Switch to Pexels or Picsum immediately.

## 5. Key Principle

Unless the user's request explicitly involves **interacting with a UI** (clicking buttons, logging into a portal, filling forms, navigating a dashboard), Playwright/browser tools are the WRONG tool for image delivery. Use web search + direct URL extraction + Markdown embed instead.
