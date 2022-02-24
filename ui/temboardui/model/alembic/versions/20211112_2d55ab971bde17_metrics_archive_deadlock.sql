SET search_path TO monitoring, public;

CREATE OR REPLACE FUNCTION archive_current_metrics(table_name TEXT, record_type TEXT, query TEXT) RETURNS TABLE(tblname TEXT, nb_rows INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
  v_table_current TEXT;
  v_table_history TEXT;
  v_query TEXT;
  i INTEGER;
BEGIN
  v_table_current := table_name || '_current';
  v_table_history := table_name || '_history';
  -- Lock _current table to prevent concurrent updates
  EXECUTE 'LOCK TABLE ' || v_table_current || ' IN SHARE MODE NOWAIT';
  v_query := replace(query, '#history_table#', v_table_history);
  v_query := replace(v_query, '#current_table#', v_table_current);
  v_query := replace(v_query, '#record_type#', record_type);
  -- Move data into _history table
  EXECUTE v_query;
  GET DIAGNOSTICS i = ROW_COUNT;
  -- Truncate _current table
  EXECUTE 'TRUNCATE '||v_table_current;
  -- Return each history table name and the number of rows inserted
  RETURN QUERY SELECT v_table_history, i;
END;
$$;

DROP FUNCTION IF EXISTS history_tables();

CREATE OR REPLACE FUNCTION aggregate_data_single(table_name TEXT, record_type TEXT, query TEXT) RETURNS TABLE(tblname TEXT, nb_rows INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
  v_agg_periods TEXT[] := array['30m', '6h'];
  v_agg_table TEXT;
  i_period TEXT;
  v_query TEXT;
  i INTEGER;
BEGIN
  -- Build and run 'aggregate' query for type of metric.
  FOREACH i_period IN ARRAY v_agg_periods LOOP
    v_agg_table := table_name || '_' || i_period || '_current';
    v_query := replace(query, '#agg_table#', v_agg_table);
    v_query := replace(v_query, '#interval#', i_period);
    v_query := replace(v_query, '#record_type#', record_type);
    v_query := replace(v_query, '#name#', table_name);
    EXECUTE v_query;
    GET DIAGNOSTICS i = ROW_COUNT;
    RETURN QUERY SELECT v_agg_table, i;
  END LOOP;
END;
$$;

DROP FUNCTION IF EXISTS aggregate_data();
