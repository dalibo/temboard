SELECT
  COUNT(DISTINCT ms.role_name) = 1 AS has_dba
FROM application.instances AS i
JOIN application.environments AS e ON e.id = i.environment_id
JOIN application.groups AS g ON g.id = e.dba_group_id
JOIN application.memberships AS ms ON ms.group_id = g.id
WHERE i.id = :instance_id AND ms.role_name = :role_name;
