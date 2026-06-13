# 🔍 Option 4 Setup Guide: Tavily Web Intelligence Integration

This guide provides instructions to connect your ISF-Core engine with the **Tavily Search Engine API**. This enables your AI agents to perform real-time web searches, recursive deep research, and crawl official development documentations to bypass LLM knowledge cut-off barriers.

## Why Setup Tavily Integration?
* **Up-to-Date Coding:** Allows coding agents to crawl live documentations of popular frameworks (such as React 19, Next.js, or Supabase), completely avoiding outdated or deprecated coding syntax.
* **Deep Research Workflows:** Unlocks multi-step recursive searches that crawl, synthesize, and compile insights into comprehensive market analyses or technical dossiers.
* **Autonomous Troubleshooting:** When a self-healing compiler error is obscure, the agent can search the web for StackOverflow threads or GitHub issues detailing the exact solution.

---

## Step 1: Obtain a Tavily API Key

1. Go to the [Tavily Developer Portal](https://tavily.com).
2. Sign up for a developer account (Tavily provides a generous free tier of search queries monthly).
3. Navigate to your Developer Dashboard and copy your **API Key** (it starts with `tvly-`).

---

## Step 2: Configure Environment Variables

Update your `.env` file at the root of your `isf-core` directory to include your Tavily credentials:

1. Open `.env`:
   ```bash
   nano .env
   ```
2. Enable and fill in the Tavily variable:
   ```env
   # Tavily Search API Key
   TAVILY_API_KEY=tvly-your-tavily-api-key-here
   ```

---

## Step 3: Verify Search Operations

You can test if your search engine is working using the interactive workspace console or by invoking a search command via your dashboard chat:

1. Open the ISF-Core Web Workspace (`http://localhost:3001`).
2. Ask your agent:
   > *"Run deep research on the differences between React 18 and React 19 server components."*
3. The engine will spin up a research worker, execute parallel web queries, scrape relevant articles, synthesize the facts, and output a detailed Markdown report with inline citations!
