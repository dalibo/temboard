SET search_path TO monitoring, public;

BEGIN;

CREATE TYPE check_state_type AS ENUM('OK', 'WARNING', 'CRITICAL', 'UNDEF');

CREATE TYPE check_results_record AS (
	datetime TIMESTAMPTZ,
	state check_state_type,
	key VARCHAR(64),
	value REAL,
	threshold REAL
);

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

CREATE TABLE check_results_current (
	datetime TIMESTAMPTZ,
	check_id INTEGER NOT NULL REFERENCES checks (check_id),
	record check_results_record
);

CREATE TABLE check_results_history (
	history_range TSTZRANGE NOT NULL,
	check_id INTEGER NOT NULL REFERENCES checks (check_id),
	records check_results_record[]
);

CREATE OR REPLACE FUNCTION history_check_results() RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
	t JSON;
	v_table_current TEXT;
	v_table_history TEXT;
	v_query TEXT;
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

COMMIT;
