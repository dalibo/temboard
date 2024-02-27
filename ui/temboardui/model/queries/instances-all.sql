SELECT
 agent_address,
 agent_port,
 hostname,
 pg_port,
 notify,
 comment,
 discover,
 discover_date,
 discover_etag
FROM application.instances
ORDER BY 1, 2;
