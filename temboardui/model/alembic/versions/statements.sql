DROP SCHEMA IF EXISTS statements CASCADE;
CREATE SCHEMA statements;
SET search_path TO statements, public;


BEGIN;

CREATE TABLE statements (
  agent_address TEXT NOT NULL,
  agent_port INTEGER NOT NULL,
  queryid BIGINT NOT NULL,
  query TEXT NOT NULL,
  dbid OID NOT NULL,
  datname TEXT NOT NULL,
  userid OID NOT NULL,
  rolname TEXT NOT NULL,
  FOREIGN KEY (agent_address, agent_port) REFERENCES application.instances (agent_address, agent_port) ON DELETE CASCADE ON UPDATE CASCADE,
  PRIMARY KEY (agent_address, agent_port, queryid, dbid, userid)
);

CREATE TYPE statements_history_record AS (
  ts TIMESTAMP WITH TIME ZONE,
  calls BIGINT,
  total_time DOUBLE PRECISION,
  rows BIGINT,
  shared_blks_hit BIGINT,
  shared_blks_read BIGINT,
  shared_blks_dirtied BIGINT,
  shared_blks_written BIGINT,
  local_blks_hit BIGINT,
  local_blks_read BIGINT,
  local_blks_dirtied BIGINT,
  local_blks_written BIGINT,
  temp_blks_read BIGINT,
  temp_blks_written BIGINT,
  blk_read_time DOUBLE PRECISION,
  blk_write_time DOUBLE PRECISION
);

CREATE UNLOGGED TABLE statements_src_tmp (
  agent_address TEXT NOT NULL,
  agent_port INTEGER NOT NULL,
  ts  TIMESTAMP WITH TIME ZONE NOT NULL,
  userid oid NOT NULL,
  rolname TEXT NOT NULL,
  dbid oid NOT NULL,
  datname TEXT NOT NULL,
  queryid BIGINT NOT NULL,
  query TEXT NOT NULL,
  calls BIGINT NOT NULL,
  total_time DOUBLE PRECISION NOT NULL,
  rows BIGINT NOT NULL,
  shared_blks_hit BIGINT NOT NULL,
  shared_blks_read BIGINT NOT NULL,
  shared_blks_dirtied BIGINT NOT NULL,
  shared_blks_written BIGINT NOT NULL,
  local_blks_hit BIGINT NOT NULL,
  local_blks_read BIGINT NOT NULL,
  local_blks_dirtied BIGINT NOT NULL,
  local_blks_written BIGINT NOT NULL,
  temp_blks_read BIGINT NOT NULL,
  temp_blks_written BIGINT NOT NULL,
  blk_read_time DOUBLE PRECISION NOT NULL,
  blk_write_time DOUBLE PRECISION NOT NULL
);

CREATE TABLE statements_history_current (
  agent_address TEXT NOT NULL,
  agent_port INTEGER NOT NULL,
  queryid BIGINT NOT NULL,
  dbid OID NOT NULL,
  userid OID NOT NULL,
  record statements_history_record NOT NULL,
  FOREIGN KEY (agent_address, agent_port, queryid, dbid, userid) REFERENCES statements ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE statements_history_current_db (
  agent_address TEXT NOT NULL,
  agent_port INTEGER NOT NULL,
  dbid OID NOT NULL,
  datname TEXT NOT NULL,
  record statements_history_record NOT NULL,
  FOREIGN KEY (agent_address, agent_port) REFERENCES application.instances (agent_address, agent_port) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE OR REPLACE FUNCTION statements_snapshot(_address text, _port integer) RETURNS void AS $PROC$
DECLARE
    v_rowcount    bigint;
BEGIN
    -- In this function, we capture statements, and also aggregate counters by database

    WITH capture AS(
        SELECT *
        FROM statements.statements_src_tmp
        WHERE agent_address = _address AND agent_port = _port
    ),

    missing_statements AS (
        INSERT INTO statements.statements (agent_address, agent_port, queryid, query, dbid, datname, userid, rolname)
            SELECT _address, _port, queryid, query, dbid, datname, userid, rolname
            FROM capture c
            ON CONFLICT DO NOTHING
    ),

    by_query AS (
        INSERT INTO statements.statements_history_current
            SELECT _address, _port, queryid, dbid, userid,
            ROW(
                ts, calls, total_time, rows, shared_blks_hit, shared_blks_read,
                shared_blks_dirtied, shared_blks_written, local_blks_hit, local_blks_read,
                local_blks_dirtied, local_blks_written, temp_blks_read, temp_blks_written,
                blk_read_time, blk_write_time
            )::statements.statements_history_record AS record
            FROM capture
    ),

    by_database AS (
        INSERT INTO statements.statements_history_current_db
            SELECT _address, _port, dbid, datname,
            ROW(
                ts, sum(calls), sum(total_time), sum(rows), sum(shared_blks_hit), sum(shared_blks_read),
                sum(shared_blks_dirtied), sum(shared_blks_written), sum(local_blks_hit), sum(local_blks_read),
                sum(local_blks_dirtied), sum(local_blks_written), sum(temp_blks_read), sum(temp_blks_written),
                sum(blk_read_time), sum(blk_write_time)
            )::statements.statements_history_record AS record
            FROM capture
            GROUP BY dbid, datname, ts
    )

    SELECT count(*) INTO v_rowcount
    FROM capture;

    DELETE FROM statements.statements_src_tmp WHERE agent_address = _address AND agent_port = _port;
END;
$PROC$ language plpgsql; /* end of statements_snapshot */

COMMIT;
