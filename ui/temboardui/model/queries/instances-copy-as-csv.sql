COPY (
  WITH
		inventory AS (SELECT DISTINCT
			i.hostname AS "Hostname",
			i.pg_port AS "Port",
			i.discover->'postgres'->'data_directory'#>>'{}' AS "PGDATA",
			i.discover->'postgres'->'version_summary'#>>'{}' AS "Version",
			e.name AS "Environment",
			i.agent_address AS "Agent Address",
			i.agent_port AS "Agent Port",
			string_agg(DISTINCT plugin_name, ',') AS "Plugins",
			i.comment AS "Comment"
		FROM application.instances AS i
		JOIN application.environments AS e ON e.id = i.environment_id
		LEFT OUTER JOIN application.plugins
				ON plugins.agent_address = i.agent_address
				AND plugins.agent_port = i.agent_port
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
