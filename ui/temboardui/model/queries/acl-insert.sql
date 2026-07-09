INSERT INTO
  application.acl(role, action, resource, deny)
VALUES
  (:role, :action, :resource, :deny)
RETURNING *;