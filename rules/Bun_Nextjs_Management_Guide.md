# 🍞 Bun & Next.js Management Guide

## Objective
This document outlines the standard protocol for managing Next.js frontend projects within this repository using **Bun** as the primary package manager and runtime. It ensures fast dependency resolution, prevents lockfile conflicts, and provides a stable development environment.

## 1. Core Directives

*   **ALWAYS use Bun:** You MUST use `bun` for all package management tasks instead of `npm`, `yarn`, or `pnpm`.
*   **Lockfile Exclusivity:** The repository relies on `bun.lockb` for dependency resolution. You MUST NEVER generate or commit `package-lock.json` or `yarn.lock`. If you see them, delete them.
*   **Running Scripts:** Execute all `package.json` scripts using `bun run <script_name>`.
*   **Next.js Telemetry:** To avoid network timeout crashes during local development, ALWAYS disable Next.js telemetry by setting `NEXT_TELEMETRY_DISABLED=1` when running the dev server.
*   **Port Configuration:** When starting Next.js, explicitly bind the port using the `--port` flag (e.g., to avoid conflicts with standard port 3000 used by other apps).

## 2. Common Commands

| Task | Bun Command |
| :--- | :--- |
| **Install all dependencies** | `bun install` |
| **Add a new package** | `bun add <package-name>` |
| **Add a dev dependency** | `bun add -d <package-name>` |
| **Remove a package** | `bun remove <package-name>` |
| **Start Development Server** | `NEXT_TELEMETRY_DISABLED=1 bun run dev --port 3011` |
| **Build for Production** | `bun run build` |
| **Start Production Server** | `bun run start` |

## 3. Examples

### 🟢 Good Examples
*   Adding a Tailwind plugin: `bun add -d tailwind-scrollbar`
*   Starting the dev server safely: `NEXT_TELEMETRY_DISABLED=1 bun run dev --port 3011`
*   Cleaning up old setups before migrating to bun: `rm -rf node_modules package-lock.json && bun install`

### 🔴 Bad Examples
*   **Bad:** Running `npm install`, which generates a conflicting `package-lock.json`.
*   **Bad:** Running `npm run dev`, which uses Node.js instead of the faster Bun runtime.
*   **Bad:** Running Next.js without disabling telemetry on restricted networks, causing `UND_ERR_CONNECT_TIMEOUT` crashes.


## 4. Standard Development Script

To ensure all the above directives (telemetry disabling, port selection, bun usage) are executed consistently by all developers and AI agents, the standard way to launch the frontend is by using the provided shell script: `frontend/run_bun_dev.sh`.

### `frontend/run_bun_dev.sh` Reference:
```bash
#!/bin/bash
# Navigate to the script's directory (frontend folder)
cd "$(dirname "$0")"

echo "📦 Installing dependencies with Bun..."
# Install dependencies using bun
bun install

echo "🚀 Starting Next.js development server on port 3011..."
# Disable Next.js telemetry to prevent network timeout warnings
export NEXT_TELEMETRY_DISABLED=1

# Start dev server on port 3011
bun run dev --port 3011
```

**CRITICAL INSTRUCTION:** 
Whenever asked to run or start the frontend, AI agents MUST execute `./run_bun_dev.sh` (from within the frontend folder) rather than manually constructing the bun dev command.

## 5. Environment Variables & API Routing

*   **No Hardcoded Ports or URLs:** You MUST NEVER hardcode API URLs, WebSocket endpoints, or ports directly inside React/Next.js components (e.g., do not use `http://localhost:8011` directly in a `.tsx` file).
*   **Environment Files:** Always use `.env.local` to define backend connections using the `NEXT_PUBLIC_` prefix so they are accessible in the browser.
*   **Implementation Standard:** Define fallback patterns inside the code when reading environment variables to ensure the app doesn't crash if an environment variable is temporarily missing.

### 🟢 Good Example (Dynamic & Scalable):
```typescript
// frontend/components/Example.tsx
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8011";
const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8011";

const response = await fetch(`${API_BASE}/api/v1/data`);
const ws = new WebSocket(`${WS_BASE}/ws/v1/stream`);
```

### 🔴 Bad Example (Hardcoded & Brittle):
```typescript
// frontend/components/Example.tsx
// BAD: Will break if the backend port changes or when deployed to production.
const response = await fetch("http://localhost:8011/api/v1/data");
const ws = new WebSocket("ws://localhost:8011/ws/v1/stream");
```