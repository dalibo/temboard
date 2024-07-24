SELECT
	agent_address,
	agent_port,
	hostname,
	pg_port,
	notify,
	comment,
	discover,
	discover_date,
	discover_etag,
	environment_id,
	e.id AS e_id,
	e.name AS e_name
  FROM application.instances AS i
  JOIN application.environments AS e ON e.id = i.environment_id
 ORDER BY 1, 2;
