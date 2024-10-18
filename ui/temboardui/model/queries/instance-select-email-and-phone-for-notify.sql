SELECT
	array_agg(DISTINCT r.role_email) FILTER (WHERE r.role_email IS NOT NULL AND r.role_email <> '') AS emails,
	array_agg(DISTINCT r.role_phone) FILTER (WHERE r.role_phone IS NOT NULL AND r.role_phone <> '') AS phones
  FROM application.instances AS i
  JOIN application.environments AS e ON i.environment_id = e.id
  JOIN application.memberships AS m ON e.dba_group_id = m.group_id
  JOIN application.roles AS r ON m.role_name = r.role_name
 WHERE i.agent_address = :agent_address AND i.agent_port = :agent_port
   AND r.is_active AND i.notify;
