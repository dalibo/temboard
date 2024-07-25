SELECT
	array_agg(DISTINCT r.role_email) FILTER (WHERE r.role_email IS NOT NULL AND r.role_email <> '') AS emails,
	array_agg(DISTINCT r.role_phone) FILTER (WHERE r.role_phone IS NOT NULL AND r.role_phone <> '') AS phones
  FROM application.instance_groups AS ixg
  JOIN application.access_role_instance AS ari
    ON ari.instance_group_name = ixg.group_name AND ari.instance_group_kind = ixg.group_kind
  JOIN application.role_groups AS rxg
    ON rxg.group_name = ari.role_group_name AND rxg.group_kind = ari.role_group_kind
  JOIN application.roles AS r
    ON r.role_name = rxg.role_name
 WHERE ixg.agent_address = :agent_address AND ixg.agent_port = :agent_port
   AND r.is_active;
