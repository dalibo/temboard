WITH "group" AS (
	SELECT id, description FROM application.groups WHERE name = :group
)
INSERT INTO application.memberships (role_name, group_id)
SELECT :role, id FROM "group" AS g;
