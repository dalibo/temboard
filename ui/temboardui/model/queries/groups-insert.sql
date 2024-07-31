INSERT INTO application.groups (group_kind, group_name, group_description)
VALUES (:kind, :name, :description)
RETURNING *;
