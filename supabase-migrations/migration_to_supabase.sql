-- Migration Script: SQLite to Supabase
-- Includes cron_scheduled_jobs seed data

--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8
-- Dumped by pg_dump version 15.8

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: cron_scheduled_jobs; Type: TABLE DATA; Schema: public; Owner: supabase_admin
--

INSERT INTO public.cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, target_payload, version, created_by, updated_by, created_at, updated_at, is_deleted, deleted_at, job_type) VALUES (19, 'Auto Agent Task', NULL, '*/5 * * * *', false, 'ISOLATED_PROCESS', '"{\"module\": \"cron_tasks.auto_agent_task\"}"', 1, NULL, NULL, '2026-06-07 02:46:19.140797+00', '2026-06-30 00:42:44.681349+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, target_payload, version, created_by, updated_by, created_at, updated_at, is_deleted, deleted_at, job_type) VALUES (26, 'browser_session_cleanup', NULL, '*/15 * * * *', false, 'ISOLATED_PROCESS', '"{\"module\": \"cron_tasks.browser_session_cleanup\"}"', 1, NULL, NULL, '2026-06-29 09:27:20.306937+00', '2026-06-30 00:43:12.15515+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, target_payload, version, created_by, updated_by, created_at, updated_at, is_deleted, deleted_at, job_type) VALUES (24, 'Token Usage Housekeeping', NULL, '1,2 * * * *', false, 'ISOLATED_PROCESS', '"{\"module\": \"cron_tasks.token_usage_housekeeping\"}"', 1, NULL, NULL, '2026-06-08 01:53:01.467572+00', '2026-06-30 00:43:54.574833+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, target_payload, version, created_by, updated_by, created_at, updated_at, is_deleted, deleted_at, job_type) VALUES (11, 'log_housekeeping', 'Prunes database logs older than 3 days directly in the Database engine', '0 */3 * * *', false, 'ISOLATED_PROCESS', '{"module": "cron_tasks.log_housekeeping"}', 1, NULL, NULL, '2026-05-27 04:58:42.563351+00', '2026-06-30 04:12:41.872795+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, target_payload, version, created_by, updated_by, created_at, updated_at, is_deleted, deleted_at, job_type) VALUES (16, 'Auto Sonar Issue Fixer', 'Automatically fixes Sonar issues in the codebase in a loop (max 10 iterations) every 15 minutes.', '7 * * * *', false, 'ISOLATED_PROCESS', '"{\"module\": \"cron_tasks.sonar_fix_task\"}"', 1, NULL, NULL, '2026-05-27 07:38:13.791954+00', '2026-07-01 04:04:57.112448+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs (id, job_name, description, cron_expression, is_active, target_type, target_payload, version, created_by, updated_by, created_at, updated_at, is_deleted, deleted_at, job_type) VALUES (17, 'Auto Test Coverage Enhancer', 'Autonomously writes, runs, and self-heals unit/component tests to improve codebase coverage.', '37 * * * *', false, 'ISOLATED_PROCESS', '"{\"module\": \"cron_tasks.test_coverage_task\"}"', 1, NULL, NULL, '2026-05-29 02:25:56.663455+00', '2026-07-01 04:09:34.073576+00', false, NULL, 'Cron_Daemon');


--
-- Name: cron_scheduled_jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: supabase_admin
--

SELECT pg_catalog.setval('public.cron_scheduled_jobs_id_seq', 35, true);


--
-- PostgreSQL database dump complete
--

