SELECT
 e.id,
 e.name
FROM application.environments AS e
JOIN application.groups AS g ON g.id = e.dba_group_id
JOIN application.memberships AS ms ON ms.group_id = g.id
WHERE ms.role_name = :role_name;
