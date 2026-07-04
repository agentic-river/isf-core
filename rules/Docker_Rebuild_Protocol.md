# 🐳 Docker Rebuild Protocol

## Objective
This document defines the strict protocol for AI agents regarding Docker container lifecycle management.

## Rule
Whenever an AI agent modifies any of the following dependency or environment files:
- `requirements.txt`
- `requirements.in`
- `package.json`
- `package-lock.json`
- `Dockerfile`
- `docker-compose.yml` or `compose.yml`
- `.env` or `.env.local`

The agent MUST autonomously execute the following command to rebuild and restart the affected containers:
```bash
docker compose build && docker compose up -d
```

## Exceptions
**CRITICAL EXCEPTION:** Do NOT attempt to restart the following core infrastructure containers autonomously:
- `isf-dev`
- `isf-prod`
- `isf-core`
- `ai-proxy`
- `isf-ai-proxy`

If changes affect these containers, the AI agent MUST explicitly inform the user and request that the user performs the restart manually.

## Validation
Do NOT proceed to further testing or verification until the containers have been successfully rebuilt and restarted. You must monitor the logs or use `docker compose ps` to ensure the containers are running and healthy before assuming the new dependencies are active.