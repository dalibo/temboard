BEGIN;

CREATE TABLE IF NOT EXISTS monitoring.collector_status (
  instance_id INTEGER PRIMARY KEY REFERENCES monitoring.instances(instance_id) ON DELETE CASCADE,
  last_pull TIMESTAMP WITHOUT TIME ZONE,
  last_push TIMESTAMP WITHOUT TIME ZONE,
  last_insert TIMESTAMP WITHOUT TIME ZONE,
  status CHAR(12) CHECK (status = 'OK' OR status = 'FAIL')
);

GRANT ALL ON TABLE monitoring.collector_status TO temboard;

COMMIT;
