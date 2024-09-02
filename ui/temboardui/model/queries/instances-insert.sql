WITH environment AS (
    SELECT id FROM application.environments WHERE name = :environment
)
INSERT INTO application.instances (agent_address, agent_port, hostname, pg_port, notify, comment, discover, discover_date, discover_etag, environment_id)
SELECT
    :agent_address AS agent_address,
    :agent_port AS agent_port,
    :hostname AS hostname,
    :pg_port AS pg_port,
    :notify AS notify,
    :comment AS "comment",
    :discover AS discover,
    :discover_date AS discover_date,
    :discover_etag AS discover_etag,
    environment.id AS environment_id
FROM environment
RETURNING *;
