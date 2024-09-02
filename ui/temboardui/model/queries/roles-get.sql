SELECT
	r.role_name,
	role_email,
	role_phone,
	is_active,
	is_admin,
	g.id AS g_id,
	g.name,
	e.id AS e_id,
	e.name AS e_name
  FROM application.roles AS r
  LEFT OUTER JOIN application.memberships AS ms ON ms.role_name = r.role_name
  LEFT OUTER JOIN application.groups AS g ON g.id = ms.group_id
  LEFT OUTER JOIN application.environments AS e ON e.dba_group_id = g.id
 WHERE r.role_name = :name;
