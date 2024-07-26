INSERT INTO application.instance_groups (agent_address, agent_port, group_kind, group_name)
VALUES
(:agent_address, :agent_port, :group_kind, :group_name)
RETURNING *;
