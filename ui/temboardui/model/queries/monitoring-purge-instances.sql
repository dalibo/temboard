WITH deleted AS (
  SELECT
		i.instance_id,
		h.hostname,
		i.port
    FROM monitoring.instances AS i
    JOIN monitoring.hosts AS h USING (host_id)
    LEFT OUTER JOIN application.instances AS agent
      ON agent.hostname = h.hostname AND agent.pg_port = i.port
   WHERE agent.agent_address IS NULL
)
DELETE FROM monitoring.instances AS i
 USING deleted
 WHERE i.instance_id = deleted.instance_id
       RETURNING deleted.hostname, deleted.port;
