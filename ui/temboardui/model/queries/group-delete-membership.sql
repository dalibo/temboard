DELETE FROM application.memberships AS ms
 USING application.groups AS g
 WHERE g.name = :group AND ms.group_id = g.id AND ms.role_name = :role;
