SELECT DISTINCT
	i.agent_address,
	i.agent_port,
	i.hostname,
	i.pg_port,
	i.notify,
	i.comment,
	i.discover,
	i.discover_date,
	i.discover_etag,
	i.environment_id,
	-- Instance.plugins eager load.
	p.agent_address AS p_agent_address,
	p.agent_port AS p_agent_port,
	p.plugin_name AS p_name,
	-- Instance.environment eager load.
	e.id AS e_id,
	e.name AS e_name,
	e.description AS e_description,
	e.color AS e_color,
	e.dba_group_id AS e_dba_group_id,
	-- Environment.dba_group eager load.
	g.id AS g_id,
	g.name AS g_name,
	g.description AS g_description
  FROM application.instances AS i
  LEFT OUTER JOIN application.plugins AS p ON p.agent_address = i.agent_address AND p.agent_port = i.agent_port
  JOIN application.environments AS e ON i.environment_id = e.id
  JOIN application.groups AS g ON g.id = e.dba_group_id
 WHERE i.agent_address = :address AND i.agent_port = :port;
