INSERT INTO application.instances (agent_address, agent_port, hostname, pg_port, notify, comment, discover, discover_date, discover_etag) VALUES
(:agent_address, :agent_port, :hostname, :pg_port, :notify, :comment, :discover, :discover_date, :discover_etag)
RETURNING *;
