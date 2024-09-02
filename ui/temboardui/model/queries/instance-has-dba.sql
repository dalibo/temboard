SELECT EXISTS (
	SELECT COUNT(1)
	  FROM application.instances AS i
	  JOIN application.environments AS e ON e.id = i.environment_id
	  JOIN application.groups AS g ON g.id = e.dba_group_id
	  JOIN application.memberships AS ms ON ms.group_id = g.id
	 WHERE i.agent_address = :agent_address AND i.agent_port = :agent_port
	   AND ms.role_name = :role_name
) AS has_dba;
