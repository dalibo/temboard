SET search_path TO monitoring, public;

DROP TYPE IF EXISTS check_state_type CASCADE;
DROP TABLE IF EXISTS state_changes CASCADE;
DROP TABLE IF EXISTS check_changes CASCADE;
DROP TABLE IF EXISTS check_states CASCADE;
DROP TABLE IF EXISTS checks CASCADE;

CREATE TYPE check_state_type AS ENUM('OK', 'WARNING', 'CRITICAL', 'UNDEF');

CREATE TABLE checks (
  check_id SERIAL PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE CASCADE,
  instance_id INTEGER REFERENCES instances (instance_id) ON DELETE CASCADE,
  enabled BOOLEAN NOT NULL DEFAULT false,
  name VARCHAR(64) NOT NULL,
  warning REAL,
  critical REAL,
  description TEXT
);
CREATE INDEX idx_checks_host_instance ON checks (host_id, instance_id);


CREATE TABLE check_states (
  check_id INTEGER NOT NULL REFERENCES checks (check_id) ON DELETE CASCADE,
  key VARCHAR(64),
  state check_state_type DEFAULT 'UNDEF',
  PRIMARY KEY (check_id, key)
);


CREATE TABLE state_changes (
  datetime TIMESTAMPTZ,
  check_id INTEGER NOT NULL REFERENCES checks (check_id) ON DELETE CASCADE,
  state check_state_type,
  key VARCHAR(64),
  value REAL,
  warning REAL,
  critical REAL
);

CREATE INDEX idx_state_changes ON state_changes (datetime, check_id, key);

CREATE TABLE check_changes (
  datetime TIMESTAMPTZ,
  check_id INTEGER NOT NULL REFERENCES checks (check_id) ON DELETE CASCADE,
  enabled BOOLEAN NOT NULL DEFAULT false,
  warning REAL,
  critical REAL,
  description TEXT
);
CREATE INDEX idx_check_changes ON check_changes (datetime, check_id);


CREATE OR REPLACE FUNCTION append_state_changes(i_datetime TIMESTAMPTZ, i_check_id INTEGER,  i_state check_state_type, i_key VARCHAR(64), i_value REAL, i_warning REAL, i_critical REAL) RETURNS BOOL
LANGUAGE plpgsql
AS $$
DECLARE
  r RECORD;
BEGIN
  SELECT * INTO r FROM monitoring.state_changes WHERE check_id = i_check_id AND key = i_key ORDER BY datetime DESC LIMIT 1;
  IF NOT FOUND OR r.state != i_state
  THEN
    -- Store results only if state has changed
    INSERT INTO monitoring.state_changes (datetime, check_id, state, key, value, warning, critical)
    VALUES (i_datetime, i_check_id, i_state, i_key, i_value, i_warning, i_critical);
    RETURN true;
  ELSE
   RETURN false;
  END IF;
END;
$$;


CREATE OR REPLACE FUNCTION get_state_changes(i_host_id INTEGER, i_instance_id INTEGER, i_check_name VARCHAR(64), i_key VARCHAR(64), i_start_dt TIMESTAMPTZ, i_end_dt TIMESTAMPTZ) RETURNS SETOF state_changes
LANGUAGE plpgsql
AS $$
DECLARE
  v_check_id INTEGER;
  r RECORD;
BEGIN
  -- Find check_id using check's name, host_id and instance_id
  SELECT check_id INTO v_check_id
  FROM monitoring.checks
  WHERE host_id = i_host_id AND instance_id = i_instance_id AND name = i_check_name;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Check % not found for this host', i_check_name;
  END IF;
  IF i_key IS NULL THEN
    FOR r IN
      SELECT * FROM monitoring.state_changes
      WHERE check_id = v_check_id AND datetime <@ tstzrange(i_start_dt, i_end_dt)
      ORDER BY datetime DESC
    LOOP
      RETURN NEXT r;
    END LOOP;
  ELSE
    FOR r IN
      SELECT * FROM monitoring.state_changes
      WHERE check_id = v_check_id AND key = i_key AND datetime <@ tstzrange(i_start_dt, i_end_dt)
      ORDER BY datetime DESC
    LOOP
      RETURN NEXT r;
    END LOOP;
  END IF;
  RETURN;
END;
$$;


CREATE OR REPLACE FUNCTION history_check_changes() RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT'
  THEN
    INSERT INTO monitoring.check_changes (datetime, check_id, enabled, warning, critical, description)
    VALUES (NOW(), NEW.check_id, NEW.enabled, NEW.warning, NEW.critical, NEW.description);
    RETURN NULL;
  END IF;
  IF TG_OP = 'UPDATE' AND (NEW.enabled != OLD.enabled OR NEW.warning != OLD.warning OR
                           NEW.critical != OLD.critical OR NEW.description != OLD.description)
  THEN
    INSERT INTO monitoring.check_changes (datetime, check_id, enabled, warning, critical, description)
    VALUES (NOW(), NEW.check_id, NEW.enabled, NEW.warning, NEW.critical, NEW.description);
  END IF;
  RETURN NULL;
END;
$$;

CREATE TRIGGER tgr_history_check_changes AFTER INSERT OR UPDATE ON checks FOR EACH ROW EXECUTE PROCEDURE history_check_changes();


CREATE OR REPLACE FUNCTION get_check_changes(i_host_id INTEGER, i_instance_id INTEGER, i_check_name VARCHAR(64), i_start_dt TIMESTAMPTZ, i_end_dt TIMESTAMPTZ) RETURNS SETOF check_changes
LANGUAGE plpgsql
AS $$
DECLARE
  v_check_id INTEGER;
  r RECORD;
BEGIN
  -- Find check_id using check's name, host_id and instance_id
  SELECT check_id INTO v_check_id
  FROM monitoring.checks
  WHERE host_id = i_host_id AND instance_id = i_instance_id AND name = i_check_name;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Check % not found for this host', i_check_name;
  END IF;


  FOR r IN
    -- get the most recent state before range start
    (
      SELECT i_start_dt as datetime, check_id, enabled, warning, critical, description
      FROM monitoring.check_changes cc
      WHERE cc.check_id = v_check_id AND cc.datetime <= i_start_dt
      ORDER BY cc.datetime DESC
      LIMIT 1
    )
    UNION
    (
      SELECT datetime, check_id, enabled, warning, critical, description
      FROM monitoring.check_changes
      WHERE check_id = v_check_id AND datetime <@ tstzrange(i_start_dt, i_end_dt)
    )
    UNION
    -- get the most recent state before range stop
    (
      SELECT i_end_dt as datetime, check_id, enabled, warning, critical, description
      FROM monitoring.check_changes cc
      WHERE cc.check_id = v_check_id AND cc.datetime <= i_end_dt
      ORDER BY cc.datetime DESC
      LIMIT 1
    )
    ORDER BY datetime DESC
  LOOP
    RETURN NEXT r;
  END LOOP;
  RETURN;
END;
$$;

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO temboard;
GRANT ALL ON ALL TABLES IN SCHEMA monitoring TO temboard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA monitoring TO temboard;
