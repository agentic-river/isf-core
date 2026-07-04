# Context7 MCP Server Guide for AI Agents

## Objective
This document outlines the usage of the Context7 MCP Server for retrieving up-to-date code documentation. It acts as a strict directive for AI agents to avoid hallucinating APIs or library syntax and instead rely on verified documentation.

## 1. Core Principles
- **Mandatory Usage:** You MUST consult this server to fetch accurate docs whenever asked to write code using a third-party framework, package, or API.
- **No Hallucinations:** You NEVER hallucinate method signatures for recent library updates (e.g., Next.js App Router, React 19, Supabase v2, etc.).
- **No Fallback on Failure:** If `get-library-docs` returns no useful info, you MUST explicitly inform the user instead of defaulting to outdated knowledge.

## 2. Gateway Pre-Requisites (MANDATORY)
Because Context7 is hosted via a Docker MCP Gateway and runs **ephemerally** to save resources, its tools will not be available in your default tool list initially. 
You MUST perform these steps before trying to access the docs:
1. **Find:** Run `gateway_mcp_find(query="context7")` to ensure the server exists in the catalog.
2. **Add:** Run `gateway_mcp_add(name="context7", activate=True)` to spin up the container and load its tools into your session.

## 3. Available Tools
Once added, these tools will become available in your active session.

### A. `resolve-library-id`
**Purpose:** Resolves a package/product name to a Context7-compatible library ID.
**When to use:** You MUST call this function FIRST to obtain a valid Context7-compatible ID.

### B. `get-library-docs`
**Purpose:** Fetches the up-to-date documentation for the requested library.
**When to use:** Call this AFTER successfully resolving the ID.

## 4. Examples

### 🟢 Good Example
*   **Good:** Calling `gateway_mcp_find` and `gateway_mcp_add` for "context7". Then executing `resolve-library-id` for "react-router" to get the ID, followed by executing `get-library-docs` with the ID and topic "hooks", and only writing code after reading the response.

### 🔴 Bad Example
*   **Bad:** Trying to call `resolve-library-id` immediately without adding "context7" to the gateway session first.
*   **Bad:** Writing Next.js App Router or React 19 code based on internal memory without using Context7, resulting in outdated or hallucinated syntax.
*   **Bad:** Guessing the library ID format (e.g., passing "react" instead of the resolved Context7 ID) when calling `get-library-docs`.
