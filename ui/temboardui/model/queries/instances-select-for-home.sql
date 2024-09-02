WITH availability AS (
	SELECT
	  h.hostname AS hostname,
	  i.port as pg_port,
	  FIRST_VALUE(ia.available) OVER instance AS available
	FROM monitoring.hosts AS h
	JOIN monitoring.instances AS i ON i.host_id = h.host_id
	JOIN monitoring.instance_availability AS ia ON ia.instance_id = i.instance_id
	WINDOW instance AS (PARTITION BY h.hostname, i.port ORDER BY ia.datetime DESC)
), alerts AS (
	SELECT DISTINCT
	    h.hostname,
	    i.port AS pg_port,
		checks.name,
	    checks.description,
	    FIRST_VALUE(monitoring.check_states.state) OVER states AS state,
	    checks.check_id -- For window
	FROM monitoring.check_states
	JOIN monitoring.checks ON checks.check_id = check_states.check_id
	JOIN monitoring.instances AS i ON i.instance_id = checks.instance_id
	JOIN monitoring.hosts AS h ON h.host_id = i.host_id
	WHERE check_states.state = 'WARNING' OR check_states.state = 'CRITICAL'
	WINDOW states AS (PARTITION BY checks.check_id ORDER BY check_states.state DESC)
)
SELECT DISTINCT
  i.agent_address,
  i.agent_port,
  i.hostname,
  i.pg_port,
  -- Use for filtering.
  i.discover->'postgres'->'data_directory' AS pg_data,
  i.discover->'postgres'->'version' AS pg_version,
  i.discover->'postgres'->'version_summary' AS pg_version_summary,
  ia.available AS available,
  e.name AS environment,
  COALESCE(jsonb_agg(DISTINCT jsonb_build_object('name', alerts.name, 'description', alerts.description, 'state', alerts.state))
	  FILTER (WHERE alerts.name IS NOT NULL), '[]'::jsonb) AS checks,
  -- Used by InstanceCard.vue in hasMonitoring
  array_agg(DISTINCT plugins.plugin_name) AS plugins
FROM application.instances AS i
JOIN application.plugins
  ON plugins.agent_address = i.agent_address AND plugins.agent_port = i.agent_port
JOIN application.environments AS e ON e.id = i.environment_id
JOIN application.groups AS g ON g.id = e.dba_group_id
JOIN application.memberships AS ms ON ms.group_id = g.id
LEFT OUTER JOIN availability AS ia ON ia.hostname = i.hostname AND ia.pg_port = i.pg_port
LEFT OUTER JOIN alerts ON alerts.hostname = i.hostname AND alerts.pg_port = i.pg_port
WHERE
  ms.role_name = :role_name
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
