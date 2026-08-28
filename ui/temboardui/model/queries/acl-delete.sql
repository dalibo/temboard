DELETE FROM
  application.acl
WHERE
  role = :role
  AND action = :action
  AND resource = :resource RETURNING *;
