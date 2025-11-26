SELECT string_agg(datname, ', ') AS databases
  FROM pg_database
 WHERE datname NOT IN ('template1', 'postgres');
