UPDATE application.acl
SET
  resource = :after || SUBSTRING (
    resource
    FROM
      LENGTH(:before) + 1
  ) -- Keep the rest of the resource suffix
WHERE
  starts_with (resource || '/', :before || '/')
RETURNING
  *;