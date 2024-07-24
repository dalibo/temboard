SELECT
  i.agent_address,
  i.agent_port,
  i.hostname,
  i.pg_port,
  i.notify,
  i.comment,
  i.cdate,
  i.discover,
  i.discover_date,
  i.discover_etag,
  i.environment_id
FROM application.instances AS i
JOIN application.environment AS e ON e.id = i.environment_id
JOIN application.groups AS g ON g.id = e.group_id
JOIN application.memberships AS m ON m.group_id = g.id
WHERE m.role_name = :role_name;
