UPDATE application.acl
SET
  role = :after || SUBSTRING (
    role
    FROM
      LENGTH(:before) + 1
  ) -- Keep the rest of the role suffix
WHERE
  starts_with (role || '/', :before || '/')
RETURNING
  *;