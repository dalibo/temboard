SELECT
  id,
  role,
  "action",
  resource,
  deny,
  cdate,
  origin
FROM
  application.acl
WHERE
  role = ANY(:roles)
  AND "action" = ANY(:actions)
  AND resource = ANY(:resources);