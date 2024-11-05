SET search_path TO monitoring, public;
CREATE INDEX idx_state_changes_key
          ON monitoring.state_changes (check_id, key, datetime DESC);
