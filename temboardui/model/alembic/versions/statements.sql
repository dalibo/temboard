DROP SCHEMA IF EXISTS statements CASCADE;
CREATE SCHEMA statements;
SET search_path TO statements, public;


BEGIN;

CREATE TYPE statement_record AS (
  blk_read_time DOUBLE PRECISION,
  blk_write_time DOUBLE PRECISION,
  calls BIGINT,
  datname TEXT,
  dbid INTEGER,
  local_blks_hit BIGINT,
  local_blks_read BIGINT,
  local_blks_dirtied BIGINT,
  local_blks_written BIGINT,
  max_time DOUBLE PRECISION,
  mean_time DOUBLE PRECISION,
  min_time DOUBLE PRECISION,
  query TEXT,
  queryid BIGINT,
  rolname TEXT,
  rows BIGINT,
  shared_blks_hit BIGINT,
  shared_blks_read BIGINT,
  shared_blks_dirtied BIGINT,
  shared_blks_written BIGINT,
  stddev_time DOUBLE PRECISION,
  temp_blks_read BIGINT,
  temp_blks_written BIGINT,
  total_time DOUBLE PRECISION,
  userid INTEGER
);

CREATE TABLE statements_history_current (
  datetime TIMESTAMPTZ NOT NULL,
  agent_address TEXT NOT NULL,
  agent_port INTEGER NOT NULL,
  record statement_record NOT NULL,
  FOREIGN KEY (agent_address, agent_port) REFERENCES application.instances (agent_address, agent_port) ON DELETE CASCADE ON UPDATE CASCADE
);

COMMIT;
