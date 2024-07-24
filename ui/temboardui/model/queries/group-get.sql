SELECT
	id,
	name,
	description
FROM application.groups
WHERE name = :name
LIMIT 2;
