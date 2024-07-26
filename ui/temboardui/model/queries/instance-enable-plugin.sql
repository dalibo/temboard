INSERT INTO application.plugins (agent_address, agent_port, plugin_name)
VALUES (:agent_address, :agent_port, :name)
RETURNING *;
