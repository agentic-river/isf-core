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

INSERT INTO public.cron_scheduled_jobs VALUES (11, 'log_housekeeping', 'Prunes database logs older than 3 days directly in the Database engine', '0 */3 * * *', true, 'SQL_FUNCTION', '{"sql_command": "SELECT public.perform_database_log_housekeeping();"}', 1, NULL, NULL, '2026-05-27 04:58:42.563351+00', '2026-05-27 07:18:46.461876+00', false, NULL, 'PG_CRON');
INSERT INTO public.cron_scheduled_jobs VALUES (18, 'Auto Agent Session Task', NULL, '*/5 * * * *', false, 'ISOLATED_PROCESS', '{"module": "backend.tasks.auto_agent_task"}', 1, NULL, NULL, '2026-06-07 02:39:00.857742+00', '2026-06-07 07:56:48.452151+00', true, '2026-06-07 07:56:48.449069+00', 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs VALUES (19, 'Auto Agent Task', NULL, '*/5 * * * *', false, 'HTTP_WEBHOOK', '{"url": "http://127.0.0.1:8002/api/webhooks/auto_agent_loop", "body": null, "method": "POST", "headers": {}}', 1, NULL, NULL, '2026-06-07 02:46:19.140797+00', '2026-06-08 09:05:06.518493+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs VALUES (17, 'Auto Test Coverage Enhancer', 'Autonomously writes, runs, and self-heals unit/component tests to improve codebase coverage.', '*/5 * * * *', false, 'HTTP_WEBHOOK', '"{\"url\": \"http://127.0.0.1:8002/api/webhooks/test_coverage_loop\", \"method\": \"POST\", \"headers\": {}, \"body\": null}"', 1, NULL, NULL, '2026-05-29 02:25:56.663455+00', '2026-06-08 09:05:24.499234+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs VALUES (24, 'Token Usage Housekeeping', NULL, '1,2 * * * *', true, 'HTTP_WEBHOOK', '"{\"url\": \"http://localhost:8002/api/webhooks/token_housekeeping\", \"method\": \"POST\", \"headers\": {}, \"body\": null}"', 1, NULL, NULL, '2026-06-08 01:53:01.467572+00', '2026-06-09 12:32:38.964413+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs VALUES (16, 'Auto Sonar Issue Fixer', 'Automatically fixes Sonar issues in the codebase in a loop (max 10 iterations) every 15 minutes.', '*/30 * * * *', true, 'HTTP_WEBHOOK', '"{\"url\": \"http://127.0.0.1:8002/api/webhooks/sonar_fix_loop\", \"method\": \"POST\", \"headers\": {}, \"body\": null}"', 1, NULL, NULL, '2026-05-27 07:38:13.791954+00', '2026-06-09 12:32:41.530708+00', false, NULL, 'Cron_Daemon');
INSERT INTO public.cron_scheduled_jobs VALUES (10, 'growth_analysis', 'Runs Growth Agent and Architect Agent analysis (Triggered via pg_cron Webhook callback)', '0 * * * *', false, 'HTTP_WEBHOOK', '{"url": "http://backend:8001/api/admin/cron/tasks/growth-analysis", "headers": {"X-Cron-Secret": "1ppzTwXygDbVB75ClTHfNazix8mP0aKoDHZp2IG-jlE"}}', 1, NULL, NULL, '2026-05-27 04:58:42.563351+00', '2026-06-13 01:59:48.731378+00', false, NULL, 'PG_CRON');


--
-- Name: cron_scheduled_jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: supabase_admin
--

SELECT pg_catalog.setval('public.cron_scheduled_jobs_id_seq', 25, true);


--
-- PostgreSQL database dump complete
--

