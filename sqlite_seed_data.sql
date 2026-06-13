-- SQLite Seed Data Script
-- Destroys existing records in the target tables and imports preset defaults for browser_credentials and cron_scheduled_jobs.

-- ==========================================
-- 1. Create tables if they do not exist
-- ==========================================

CREATE TABLE IF NOT EXISTS browser_credentials (
    id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    environment TEXT DEFAULT 'production',
    username TEXT NOT NULL,
    password_encrypted TEXT NOT NULL,
    input_schema TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cron_scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    cron_expression TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    target_type TEXT NOT NULL,
    job_type TEXT NOT NULL,
    target_payload TEXT DEFAULT '{}',
    target_payload_json TEXT DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. Clear old entries
-- ==========================================

DELETE FROM browser_credentials;
DELETE FROM cron_scheduled_jobs;

-- ==========================================
-- 3. Populate Vault Credentials
-- ==========================================


-- ==========================================
-- 4. Populate Scheduled Tasks
-- ==========================================

INSERT INTO cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, job_type, target_payload, target_payload_json, is_deleted)
VALUES (
    2,
    'Auto Agent Session Task',
    'Executes dynamic agent sessions.',
    '*/5 * * * *',
    1,
    'ISOLATED_PROCESS',
    'Cron_Daemon',
    '{"module": "backend.tasks.auto_agent_task"}',
    '{"module": "backend.tasks.auto_agent_task"}',
    0
);

INSERT INTO cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, job_type, target_payload, target_payload_json, is_deleted)
VALUES (
    3,
    'Auto Test Coverage Enhancer',
    'Autonomously writes, runs, and self-heals unit/component tests to improve codebase coverage.',
    '*/5 * * * *',
    0,
    'HTTP_WEBHOOK',
    'Cron_Daemon',
    '{"url": "http://127.0.0.1:8002/api/webhooks/test_coverage_loop", "method": "POST", "headers": {}, "body": null}',
    '{"url": "http://127.0.0.1:8002/api/webhooks/test_coverage_loop", "method": "POST", "headers": {}, "body": null}',
    0
);

INSERT INTO cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, job_type, target_payload, target_payload_json, is_deleted)
VALUES (
    4,
    'Token Usage Housekeeping',
    'Runs housekeeping of recorded token counts.',
    '1,2 * * * *',
    0,
    'HTTP_WEBHOOK',
    'Cron_Daemon',
    '{"url": "http://localhost:8002/api/webhooks/token_housekeeping", "method": "POST", "headers": {}, "body": null}',
    '{"url": "http://localhost:8002/api/webhooks/token_housekeeping", "method": "POST", "headers": {}, "body": null}',
    0
);

INSERT INTO cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, job_type, target_payload, target_payload_json, is_deleted)
VALUES (
    5,
    'Auto Sonar Issue Fixer',
    'Automatically fixes Sonar issues in the codebase in a loop (max 10 iterations) every 15 minutes.',
    '*/30 * * * *',
    0,
    'HTTP_WEBHOOK',
    'Cron_Daemon',
    '{"url": "http://127.0.0.1:8002/api/webhooks/sonar_fix_loop", "method": "POST", "headers": {}, "body": null}',
    '{"url": "http://127.0.0.1:8002/api/webhooks/sonar_fix_loop", "method": "POST", "headers": {}, "body": null}',
    0
);
