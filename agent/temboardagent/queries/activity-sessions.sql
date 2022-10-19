WITH blockages AS (
	SELECT
		pid AS waiting_pid,
		-- Requires pg_blocking_pids from PostgreSQL 9.6+
		unnest(pg_blocking_pids(pid)) AS blocking_pid
	FROM pg_stat_activity
)
SELECT
  sessions.pid AS pid,
  sessions.client_addr AS client_addr,
  sessions.usename AS "username",
  sessions.application_name AS application_name,
  sessions.datname AS database,
  sessions."state" AS "state",
  sessions.backend_start AS backend_start,
  sessions.query_start AS query_start,
  sessions.query AS query,
	waiting.waiting_pid IS NOT NULL AS waiting,
	blocking.blocking_pid IS NOT NULL AS blocking
FROM pg_catalog.pg_stat_activity AS sessions
  LEFT OUTER JOIN blockages AS waiting ON waiting.waiting_pid = pid
  LEFT OUTER JOIN blockages AS blocking ON blocking.blocking_pid = pid
WHERE sessions.pid <> pg_backend_pid()
  AND sessions.backend_type = 'client backend'  -- pragma:pg_version_min 100000
ORDER BY EXTRACT(epoch FROM (NOW() - sessions.query_start)) DESC
