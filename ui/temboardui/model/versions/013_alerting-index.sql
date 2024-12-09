SET search_path TO monitoring, public;
CREATE INDEX IF NOT EXISTS idx_state_changes_key
          ON monitoring.state_changes (check_id, key, datetime DESC);
