CREATE INDEX ON statements.statements_history (agent_address, agent_port, queryid, dbid, userid);
CREATE INDEX ON statements.statements_history_current (agent_address, agent_port, queryid, dbid, userid);
CREATE INDEX ON statements.statements_history_db (agent_address, agent_port);
CREATE INDEX ON statements.statements_history_db USING GIST (coalesce_range);
CREATE INDEX ON statements.statements_history_current_db (agent_address, agent_port);
