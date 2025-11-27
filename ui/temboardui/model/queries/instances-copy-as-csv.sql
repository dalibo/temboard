COPY (
  WITH
		inventory AS (SELECT DISTINCT
      i.hostname AS "Hostname",
      port AS "Port",
      discover->'postgres'->'data_directory'#>>'{}' AS "PGDATA",
      discover->'postgres'->'version_summary'#>>'{}' AS "Version",
      e.name AS "Environment",
      app.agent_address AS "Agent Address",
      app.agent_port AS "Agent Port",
      string_agg(DISTINCT plugins.plugin_name, ',') AS "Plugins",
      app.comment AS "Comment",
      string_agg(DISTINCT db.dbname, ',') AS "Databases"
    FROM monitoring.hosts AS i
    LEFT OUTER JOIN monitoring.instances AS monit
         ON monit.host_id = i.host_id
    LEFT OUTER JOIN application.instances AS app
         ON app.hostname = i.hostname
    LEFT OUTER JOIN application.plugins
		     ON plugins.agent_address = app.agent_address
		     AND plugins.agent_port = app.agent_port
    LEFT OUTER JOIN application.environments AS e
         ON e.id = app.environment_id
    LEFT OUTER JOIN monitoring.metric_db_size_current AS db
         ON db.instance_id = monit.instance_id
         AND db.dbname NOT IN ('postgres', 'template1')
         AND datetime > (now() - interval '5 minutes')
GROUP BY 1, 2, 3, 4, 5, 6, 7
ORDER BY 5, 1, 2
	)
  SELECT * FROM inventory
	WHERE concat_ws(
		' ',
		"Hostname", "Port", "PGDATA", "Version", "Environment",
		"Agent Address", "Agent Port"
	) LIKE %s
) TO STDOUT WITH (
	DELIMITER ';',
	ENCODING 'UTF-8',
	FORCE_QUOTE *,
	FORMAT CSV,
	HEADER
) ;
