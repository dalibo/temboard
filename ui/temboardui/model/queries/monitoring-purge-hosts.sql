WITH deleted AS (
  SELECT
		h.host_id,
		h.hostname
    FROM monitoring.hosts AS h
    LEFT OUTER JOIN monitoring.instances AS i USING (host_id)
   WHERE i.instance_id IS NULL
)
DELETE FROM monitoring.hosts AS h
 USING deleted
 WHERE h.host_id = deleted.host_id
       RETURNING deleted.hostname;
