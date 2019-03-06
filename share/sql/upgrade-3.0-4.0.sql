-- Repository upgrade script from 3.0 to 4.0

BEGIN;

ALTER TABLE application.instances
ADD COLUMN pg_version_summary TEXT;

UPDATE application.instances AS a
SET pg_version_summary = (
  SELECT version
  FROM monitoring.instances AS b
  JOIN monitoring.hosts AS c
  ON b.host_id = c.host_id
  WHERE c.hostname = a.hostname
  AND b.port = a.pg_port
);

ALTER TABLE application.roles
ALTER COLUMN role_email DROP NOT NULL;

ALTER TABLE application.roles
ADD COLUMN role_phone TEXT;

COMMIT;
