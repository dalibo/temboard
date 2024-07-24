SELECT
	r.role_name AS username,
	g.name AS groupname,
	g.description AS profile
  FROM application.environments AS e
  JOIN application.groups AS g ON g.id = e.dba_group_id
  JOIN application.memberships AS ms ON ms.group_id = g.id
  JOIN application.roles AS r on r.role_name = ms.role_name
 WHERE e.name = :name
 ORDER BY 1, 2;
