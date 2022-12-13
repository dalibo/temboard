CREATE OR REPLACE FUNCTION monitoring.archive_current_metrics(table_name TEXT, record_type TEXT, query TEXT)
RETURNS TABLE(tblname TEXT, nb_rows INTEGER)
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
  EXECUTE 'LOCK TABLE ' || v_table_current || ' IN SHARE MODE';
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
