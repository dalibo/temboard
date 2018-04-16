SET search_path TO monitoring, public;

BEGIN;

DROP TYPE IF EXISTS check_state_type CASCADE;
DROP TYPE IF EXISTS check_results_record CASCADE;
DROP TABLE IF EXISTS check_results_current;
DROP TABLE IF EXISTS check_results_history;
DROP TABLE IF EXISTS check_states;
DROP TABLE IF EXISTS checks;

CREATE TYPE check_state_type AS ENUM('OK', 'WARNING', 'CRITICAL', 'UNDEF');

CREATE TABLE checks (
  check_id SERIAL PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts (host_id),
  instance_id INTEGER REFERENCES instances (instance_id),
  enabled BOOLEAN NOT NULL DEFAULT false,
  name VARCHAR(64) NOT NULL,
  threshold_w REAL,
  threshold_c REAL,
  description TEXT
);
CREATE INDEX idx_checks_host_instance ON checks (host_id, instance_id);


CREATE TABLE check_states (
  check_id INTEGER NOT NULL REFERENCES checks (check_id),
  key VARCHAR(64),
  state check_state_type DEFAULT 'UNDEF',
  PRIMARY KEY (check_id, key)
);

CREATE TYPE check_results_record AS (
  datetime TIMESTAMPTZ,
  state check_state_type,
  key VARCHAR(64),
  value REAL,
  warning REAL,
  critical REAL
);



CREATE TABLE check_results_current (
  datetime TIMESTAMPTZ,
  check_id INTEGER NOT NULL REFERENCES checks (check_id),
  record check_results_record
);

CREATE INDEX idx_check_results_current ON check_results_current (datetime, check_id);

CREATE TABLE check_results_history (
  history_range TSTZRANGE NOT NULL,
  check_id INTEGER NOT NULL REFERENCES checks (check_id),
  records check_results_record[]
);

CREATE INDEX idx_check_results_history ON check_results_history (history_range, check_id);

CREATE OR REPLACE FUNCTION history_check_results() RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
  i INTEGER;
BEGIN
  LOCK TABLE check_results_current IN SHARE MODE;
  INSERT INTO check_results_history
    SELECT
      tstzrange(min(datetime), max(datetime)),
      check_id,
      array_agg(set_datetime_record(datetime, record)::check_results_record) AS records
    FROM check_results_current
    GROUP BY date_trunc('day', datetime), 2
    ORDER BY 1,2 ASC;
  GET DIAGNOSTICS i = ROW_COUNT;
  TRUNCATE check_results_current;
  RETURN i;
END;
$$;

CREATE OR REPLACE FUNCTION insert_check_result(i_datetime TIMESTAMPTZ, i_check_id INTEGER,  i_state check_state_type, i_key VARCHAR(64), i_value REAL, i_warning REAL, i_critical REAL) RETURNS BOOL
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
  INSERT INTO monitoring.check_results_current (datetime, check_id, record)
  VALUES (i_datetime, i_check_id, (i_datetime, i_state, i_key, i_value, i_warning, i_critical)::monitoring.check_results_record);
  RETURN true;
END;
$$;

CREATE OR REPLACE FUNCTION get_check_results(i_host_id INTEGER, i_instance_id INTEGER, i_check_name VARCHAR(64), i_key VARCHAR(64), i_start_dt TIMESTAMPTZ, i_end_dt TIMESTAMPTZ) RETURNS SETOF check_results_record
LANGUAGE plpgsql
AS $$
DECLARE
  v_check_id INTEGER;
  r check_results_record%ROWTYPE;
BEGIN
  -- Find check_id using check's name, host_id and instance_id
  SELECT check_id INTO v_check_id
  FROM monitoring.checks
  WHERE host_id = i_host_id AND instance_id = i_instance_id AND name = i_check_name;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Check % not found for this host', i_check_name;
  END IF;

  FOR r IN
    -- Lookup into _current and _history tables
    WITH expand AS (
      SELECT datetime, check_id, record
      FROM monitoring.check_results_current
      WHERE check_id = v_check_id AND datetime <@ tstzrange(i_start_dt, i_end_dt)
      UNION
      SELECT (hist_query.record).datetime, check_id, hist_query.record
      FROM (
        SELECT check_id, unnest(records)::check_results_record AS record
        FROM monitoring.check_results_history
        WHERE check_id = v_check_id AND history_range && tstzrange(i_start_dt, i_end_dt)
      ) AS hist_query
    )
    SELECT (record).datetime, (record).state, (record).key, (record).value, (record).warning, (record).critical
    FROM expand
    WHERE datetime <@ tstzrange(i_start_dt, i_end_dt)
    ORDER BY datetime ASC
  LOOP
    -- Filter results on key if any
    IF i_key IS NOT NULL THEN
      IF r.key = i_key THEN
        RETURN NEXT r;
      END IF;
    ELSE
      RETURN NEXT r;
    END IF;
  END LOOP;
  RETURN;
END;
$$;

COMMIT;
