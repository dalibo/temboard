WITH blockages AS (
	SELECT
		pid AS waiting_pid,
		-- Requires pg_blocking_pids from PostgreSQL 9.6+
		unnest(pg_blocking_pids(pid)) AS blocking_pid
	FROM pg_catalog.pg_stat_activity
)
SELECT
	lock.pid,
	lock.locktype,
	dat.datname AS "database",
	nsp.nspname AS "schema",
	rel.relname AS "relation",
	lock.mode,
	lock."granted",
	waiting.blocking_pid AS blocking_pid,
	min(lock."waitstart"),  -- pragma:pg_version_min 140000
	array_remove(array_agg(blocking.waiting_pid), NULL) AS waiting_pids
FROM pg_catalog.pg_locks AS lock
	LEFT OUTER JOIN pg_catalog.pg_database AS dat ON dat.oid = lock.database
	LEFT OUTER JOIN pg_catalog.pg_class AS rel ON rel.oid = lock.relation
	LEFT OUTER JOIN pg_catalog.pg_namespace AS nsp ON nsp.oid = rel.relnamespace
	LEFT OUTER JOIN blockages AS waiting ON waiting.waiting_pid = pid
	LEFT OUTER JOIN blockages AS blocking ON blocking.blocking_pid = pid
	LEFT OUTER JOIN pg_catalog.pg_locks AS waiting_lock
		ON lock."granted" AND waiting_lock.pid = blocking.waiting_pid
			AND waiting_lock.locktype = lock.locktype
			AND CASE lock.locktype
				WHEN 'advisory' THEN waiting_lock.objid = lock.objid AND waiting_lock.objsubid = lock.objsubid
				WHEN 'relation' THEN waiting_lock.database = lock.database AND waiting_lock.relation = lock.relation
				WHEN 'transactionid' THEN waiting_lock.transactionid = lock.transactionid
				WHEN 'virtualxid' THEN waiting_lock.virtualxid = lock.virtualxid
			END
WHERE NOT lock."granted"
	OR (blocking.blocking_pid IS NOT NULL AND waiting_lock.pid IS NOT NULL AND "lock"."mode" LIKE '%Exclusive%')
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
ORDER BY min("lock"."waitstart") ASC -- pragma:pg_version_min 140000
