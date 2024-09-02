SELECT
	ms.role_name AS username,
	g.name,
	g.description AS profile
  FROM application.groups AS g
  JOIN application.memberships AS ms ON ms.group_id = g.id
 WHERE g.name = :group AND ms.role_name = :role
 ORDER BY 1, 2;
