SELECT
 DISTINCT r.role_email
FROM application.instances AS i
JOIN application.environments AS e ON e.id = i.environment_id
JOIN application.groups AS g ON g.id = e.dba_group_id
JOIN application.memberships AS ms ON ms.group_id = g.id
JOIN application.roles AS r ON r.role_name = ms.role_name
WHERE i.id = :instance_id;
