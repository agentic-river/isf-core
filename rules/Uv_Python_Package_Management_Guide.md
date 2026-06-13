# 🚀 UV Python Package Management Guide

## Objective
This document defines the strict protocol for AI agents regarding Python package and virtual environment management in this repository. Agents MUST use `uv` (by Astral) instead of the standard `pip`, `venv`, or `pip-tools` commands to ensure lightning-fast, reproducible, and reliable dependency management.

## Actionable Directives

1. **NEVER use standard `pip` or `python -m venv` commands.**
2. **ALWAYS use `uv` equivalents for environment creation and package installation.**
3. **Dependency Definition:** High-level dependencies MUST be defined in `requirements.in` without strict version pinning (unless absolutely required to avoid conflicts). 
4. **Locking Dependencies:** ALWAYS generate the locked `requirements.txt` using the `uv pip compile` command. Do not manually edit `requirements.txt`.
5. **Syncing Environments:** ALWAYS synchronize the virtual environment using `uv pip sync` rather than installing from the requirements file directly with `install -r`.

## Commands Translation Reference

Whenever you need to execute a package management command, map it to the `uv` standard:

*   **Create Virtual Environment:**
    *   🔴 **Bad:** `python -m venv .venv`
    *   🟢 **Good:** `uv venv`
*   **Install a Single Package:**
    *   🔴 **Bad:** `pip install <package_name>`
    *   🟢 **Good:** `uv pip install <package_name>`
*   **Compile Requirements (Locking):**
    *   🔴 **Bad:** `pip freeze > requirements.txt` or `pip-compile`
    *   🟢 **Good:** `uv pip compile requirements.in -o requirements.txt`
*   **Sync/Install All Requirements:**
    *   🔴 **Bad:** `pip install -r requirements.txt`
    *   🟢 **Good:** `uv pip sync requirements.txt`
*   **Run a Server/Script (Auto-detects venv):**
    *   🔴 **Bad:** `source .venv/bin/activate && uvicorn app.main:app`
    *   🟢 **Good:** `uv run uvicorn app.main:app --reload` (or use the provided `./run_pip_sync_uvicorn_app_reload.sh` script)

## Examples

### 🟢 Good Example
When a user asks to add `supabase` to the project:
1. Agent adds `supabase` to `requirements.in`.
2. Agent runs: `uv pip compile requirements.in -o requirements.txt`
3. Agent runs: `uv pip sync requirements.txt`

### 🔴 Bad Example
When a user asks to add `supabase` to the project:
1. Agent runs `pip install supabase` and tells the user to run `pip freeze > requirements.txt`. This breaks the compile/sync paradigm and introduces unnecessary, unmanaged dependencies.

## Standard Development Script (`run_pip_sync_uvicorn_app_reload.sh`)

Whenever developing or starting the backend server locally, AI agents and developers MUST use the provided standard launch script located at `backend/run_pip_sync_uvicorn_app_reload.sh`. 

This script automates compiling dependencies, syncing the virtual environment, and starting the FastAPI server using `uv`. 

**Script Reference:**
```bash
#!/bin/bash
set -e

echo "Compiling requirements.in to requirements.txt..."
uv pip compile requirements.in -o requirements.txt

echo "Syncing virtual environment..."
uv pip sync requirements.txt

echo "Starting Uvicorn server..."
uv run uvicorn app.main:app --reload --port 8011
```

**Instructions for AI Agents:**
* If you modify `requirements.in`, DO NOT manually run the compile and sync commands individually unless requested. You can simply run or instruct the user to run this script, which will automatically update `requirements.txt`, sync the environment, and boot the server.
* The backend is configured to run on **port 8011** via this script.
