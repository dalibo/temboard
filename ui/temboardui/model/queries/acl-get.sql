SELECT
  *
FROM
  application.acl
WHERE
  role = ANY(:roles)
  AND ACTION = ANY(:actions)
  AND resource = ANY(:resources);