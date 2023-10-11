SELECT
 agent_address,
 agent_port,
 agent_key,
 hostname,
 pg_port,
 notify,
 comment,
 discover,
 discover_date,
 discover_etag
FROM application.instances
ORDER BY 1, 2;
