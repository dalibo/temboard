-- Repository upgrade script from 3.0 to 4.0

BEGIN;

ALTER TABLE application.instances
ADD COLUMN pg_version_summary TEXT;

UPDATE application.instances AS a
SET pg_version_summary = (
  SELECT version
  FROM monitoring.instances AS b
  JOIN monitoring.hosts AS c
  ON b.host_id = c.host_id
  WHERE c.hostname = a.hostname
  AND b.port = a.pg_port
);

ALTER TABLE application.roles
ALTER COLUMN role_email DROP NOT NULL;

ALTER TABLE application.roles
DROP CONSTRAINT roles_role_email_key;

ALTER TABLE application.roles
ADD COLUMN role_phone TEXT;

ALTER TABLE application.instances
ADD COLUMN notify BOOLEAN NOT NULL DEFAULT true;


-- Move metric_cpu_record.time_* to BIGINT
SET search_path TO monitoring;

ALTER TYPE metric_cpu_record RENAME TO metric_cpu_record_OLD;

CREATE TYPE metric_cpu_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  time_user BIGINT,
  time_system BIGINT,
  time_idle BIGINT,
  time_iowait BIGINT,
  time_steal BIGINT
);

CREATE OR REPLACE FUNCTION cast_metric_cpu_record_bigint(i_record metric_cpu_record_OLD)
RETURNS metric_cpu_record
LANGUAGE plpgsql
AS $$

DECLARE
  r metric_cpu_record;
BEGIN
  r.datetime = i_record.datetime;
  r.measure_interval = i_record.measure_interval;
  r.time_user = i_record.time_user::BIGINT;
  r.time_system = i_record.time_system::BIGINT;
  r.time_idle = i_record.time_idle::BIGINT;
  r.time_iowait = i_record.time_iowait::BIGINT;
  r.time_steal = i_record.time_steal::BIGINT;
  RETURN r;
END;
$$;

CREATE OR REPLACE FUNCTION cast_metric_cpu_records_bigint(i_records metric_cpu_record_OLD[])
RETURNS metric_cpu_record[]
LANGUAGE plpgsql
AS $$

DECLARE
  ret metric_cpu_record[];
  r metric_cpu_record;
  r_old metric_cpu_record_OLD;
BEGIN
  FOREACH r_old IN ARRAY i_records
  LOOP
    ret := array_append(ret, cast_metric_cpu_record_bigint(r_old));
  END LOOP;
  RETURN ret;
END;
$$;

ALTER TABLE metric_cpu_current ALTER COLUMN record TYPE metric_cpu_record USING cast_metric_cpu_record_bigint(record)::metric_cpu_record;
ALTER TABLE metric_cpu_history ALTER COLUMN records TYPE metric_cpu_record[] USING cast_metric_cpu_records_bigint(records)::metric_cpu_record[];
ALTER TABLE metric_cpu_30m_current ALTER COLUMN record TYPE metric_cpu_record USING cast_metric_cpu_record_bigint(record)::metric_cpu_record;
ALTER TABLE metric_cpu_6h_current ALTER COLUMN record TYPE metric_cpu_record USING cast_metric_cpu_record_bigint(record)::metric_cpu_record;

DROP FUNCTION cast_metric_cpu_records_bigint(metric_cpu_record_OLD[]);
DROP FUNCTION cast_metric_cpu_record_bigint(metric_cpu_record_OLD);
DROP TYPE metric_cpu_record_OLD;

\ir upgrade-monitoring-purge-instances.sql

COMMIT;
