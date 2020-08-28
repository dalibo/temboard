SET search_path = 'statements';

ALTER TYPE statements_history_record RENAME ATTRIBUTE total_time to total_exec_time;
ALTER TYPE statements_history_record ADD ATTRIBUTE total_plan_time DOUBLE PRECISION;
ALTER TYPE statements_history_record ADD ATTRIBUTE wal_records bigint;
ALTER TYPE statements_history_record ADD ATTRIBUTE wal_fpi bigint;
ALTER TYPE statements_history_record ADD ATTRIBUTE wal_bytes numeric;

DROP TABLE statements_src_tmp;
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
  total_exec_time DOUBLE PRECISION NOT NULL,
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
  blk_write_time DOUBLE PRECISION NOT NULL,
  total_plan_time DOUBLE PRECISION,
  wal_records BIGINT,
  wal_fpi BIGINT,
  wal_bytes NUMERIC
);

CREATE OR REPLACE FUNCTION statements_aggregate(_address text, _port integer)
RETURNS void AS $PROC$
BEGIN

    UPDATE metas
    SET aggts = now()
    WHERE agent_address = _address AND agent_port = _port;

    -- aggregate statements table
    INSERT INTO statements_history
        SELECT agent_address, agent_port, queryid, dbid, userid,
            tstzrange(min((record).ts), max((record).ts),'[]'),
            array_agg(record),
            ROW(min((record).ts),
                min((record).calls),
                min((record).total_exec_time),
                min((record).rows),
                min((record).shared_blks_hit),
                min((record).shared_blks_read),
                min((record).shared_blks_dirtied),
                min((record).shared_blks_written),
                min((record).local_blks_hit),
                min((record).local_blks_read),
                min((record).local_blks_dirtied),
                min((record).local_blks_written),
                min((record).temp_blks_read),
                min((record).temp_blks_written),
                min((record).blk_read_time),
                min((record).blk_write_time),
                min((record).total_plan_time),
                min((record).wal_records),
                min((record).wal_fpi),
                min((record).wal_bytes))::statements_history_record,
            ROW(max((record).ts),
                max((record).calls),
                max((record).total_exec_time),
                max((record).rows),
                max((record).shared_blks_hit),
                max((record).shared_blks_read),
                max((record).shared_blks_dirtied),
                max((record).shared_blks_written),
                max((record).local_blks_hit),
                max((record).local_blks_read),
                max((record).local_blks_dirtied),
                max((record).local_blks_written),
                max((record).temp_blks_read),
                max((record).temp_blks_written),
                max((record).blk_read_time),
                max((record).blk_write_time),
                max((record).total_plan_time),
                max((record).wal_records),
                max((record).wal_fpi),
                max((record).wal_bytes))::statements_history_record
        FROM statements_history_current
        WHERE agent_address = _address AND agent_port = _port
        GROUP BY agent_address, agent_port, queryid, dbid, userid;

    DELETE FROM statements_history_current
    WHERE agent_address = _address AND agent_port = _port;

    -- aggregate db table
    INSERT INTO statements_history_db
        SELECT agent_address, agent_port, dbid, datname,
            tstzrange(min((record).ts), max((record).ts),'[]'),
            array_agg(record),
            ROW(min((record).ts),
                min((record).calls),
                min((record).total_exec_time),
                min((record).rows),
                min((record).shared_blks_hit),
                min((record).shared_blks_read),
                min((record).shared_blks_dirtied),
                min((record).shared_blks_written),
                min((record).local_blks_hit),
                min((record).local_blks_read),
                min((record).local_blks_dirtied),
                min((record).local_blks_written),
                min((record).temp_blks_read),
                min((record).temp_blks_written),
                min((record).blk_read_time),
                min((record).blk_write_time),
                min((record).total_plan_time),
                min((record).wal_records),
                min((record).wal_fpi),
                min((record).wal_bytes))::statements_history_record,
            ROW(max((record).ts),
                max((record).calls),
                max((record).total_exec_time),
                max((record).rows),
                max((record).shared_blks_hit),
                max((record).shared_blks_read),
                max((record).shared_blks_dirtied),
                max((record).shared_blks_written),
                max((record).local_blks_hit),
                max((record).local_blks_read),
                max((record).local_blks_dirtied),
                max((record).local_blks_written),
                max((record).temp_blks_read),
                max((record).temp_blks_written),
                max((record).blk_read_time),
                max((record).blk_write_time),
                max((record).total_plan_time),
                max((record).wal_records),
                max((record).wal_fpi),
                max((record).wal_bytes))::statements_history_record
        FROM statements_history_current_db
        WHERE agent_address = _address AND agent_port = _port
        GROUP BY agent_address, agent_port, dbid, datname;

    DELETE FROM statements_history_current_db
    WHERE agent_address = _address AND agent_port = _port;
 END;
$PROC$ LANGUAGE plpgsql; /* end of statements_aggregate */


CREATE OR REPLACE FUNCTION process_statements(_address text, _port integer) RETURNS void AS $PROC$
DECLARE
    v_rowcount    bigint;
    v_coalesce    integer := 100;
    agg_seq  bigint;
BEGIN
    -- In this function, we process statements that have just been rerieved
    -- from agent, and also aggregate counters by database

    -- Create new meta for agent if doesn't already exist
    INSERT INTO metas (agent_address, agent_port) VALUES (_address, _port)
    ON CONFLICT DO NOTHING;

    PERFORM prevent_concurrent_snapshot(_address, _port);

    -- Update meta with info from the current proccess (snapshot)
    UPDATE metas
    SET coalesce_seq = coalesce_seq + 1,
        snapts = now(),
        error = NULL
    WHERE agent_address = _address AND agent_port = _port
    RETURNING coalesce_seq INTO agg_seq;

    WITH capture AS(
        SELECT *
        FROM statements_src_tmp
        WHERE agent_address = _address AND agent_port = _port
    ),

    missing_statements AS (
        INSERT INTO statements (agent_address, agent_port, queryid, query, dbid, datname, userid, rolname)
            SELECT _address, _port, queryid, query, dbid, datname, userid, rolname
            FROM capture
            ON CONFLICT DO NOTHING
    ),

    by_query AS (
        INSERT INTO statements_history_current
            SELECT _address, _port, queryid, dbid, userid,
            ROW(
                ts, calls, total_exec_time, rows, shared_blks_hit, shared_blks_read,
                shared_blks_dirtied, shared_blks_written, local_blks_hit, local_blks_read,
                local_blks_dirtied, local_blks_written, temp_blks_read, temp_blks_written,
                blk_read_time, blk_write_time, total_plan_time, wal_records, wal_fpi, wal_bytes
            )::statements_history_record
            FROM capture
    ),

    by_database AS (
        INSERT INTO statements_history_current_db
            SELECT _address, _port, dbid, datname,
            ROW(
                ts, sum(calls), sum(total_exec_time), sum(rows), sum(shared_blks_hit), sum(shared_blks_read),
                sum(shared_blks_dirtied), sum(shared_blks_written), sum(local_blks_hit), sum(local_blks_read),
                sum(local_blks_dirtied), sum(local_blks_written), sum(temp_blks_read), sum(temp_blks_written),
                sum(blk_read_time), sum(blk_write_time), sum(total_plan_time), sum(wal_records), sum(wal_fpi),
                sum(wal_bytes)
            )::statements_history_record
            FROM capture
            GROUP BY dbid, datname, ts
    )

    SELECT count(*) INTO v_rowcount
    FROM capture;

    -- Coalesce datas if needed
    IF ( (agg_seq % v_coalesce ) = 0 )
    THEN
      EXECUTE format('SELECT statements_aggregate(''%s'', %s)', _address, _port);
    END IF;

    DELETE FROM statements_src_tmp WHERE agent_address = _address AND agent_port = _port;
END;
$PROC$ language plpgsql; /* end of process_statements */
