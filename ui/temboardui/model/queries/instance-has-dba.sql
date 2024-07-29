SELECT COUNT(DISTINCT rxg.role_name) = 1 AS has_dba
  FROM application.instance_groups AS ixg
  JOIN application.access_role_instance AS ari
    ON ari.instance_group_name = ixg.group_name AND ari.instance_group_kind = ixg.group_kind
  JOIN application.role_groups AS rxg
    ON rxg.group_name = ari.role_group_name AND rxg.group_kind = ari.role_group_kind
 WHERE ixg.agent_address = :agent_address AND ixg.agent_port = :agent_port AND rxg.role_name = :role_name;
