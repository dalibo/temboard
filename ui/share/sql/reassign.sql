CREATE OR REPLACE FUNCTION __reassign_schema(schema_name TEXT) returns void as $$
DECLARE r record;
BEGIN
  RAISE NOTICE 'SCHEMA %', schema_name;
  EXECUTE 'ALTER SCHEMA ' || schema_name || ' OWNER TO temboard;';

  FOR r in SELECT
      table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema = schema_name
    ORDER BY 1, 2
  LOOP
    RAISE NOTICE 'TABLE %.%', schema_name, r.table_name;
    EXECUTE 'ALTER TABLE ' || schema_name || '.' || r.table_name || ' OWNER TO temboard;';
  END LOOP;

  FOR r IN SELECT
      sequence_schema, sequence_name
    FROM information_schema.sequences
    WHERE sequence_schema = schema_name
    ORDER BY 1, 2
  LOOP
    RAISE NOTICE 'SEQUENCE %.%', schema_name, r.sequence_name;
    EXECUTE 'ALTER SEQUENCE ' || schema_name || '.' || r.sequence_name || ' OWNER TO temboard;';
  END LOOP;

  FOR r IN SELECT
      routine_schema, routine_name
    FROM information_schema.routines
    WHERE routine_schema = schema_name
    ORDER BY 1, 2
  LOOP
    RAISE NOTICE 'FUNCTION %.%', schema_name, r.routine_name;
    EXECUTE 'ALTER FUNCTION ' || schema_name || '.' || r.routine_name || ' OWNER TO temboard;';
  END LOOP;

  FOR r IN SELECT
      schemaname, indexname
    FROM pg_catalog.pg_indexes
    WHERE schemaname = schema_name
    ORDER BY 1, 2
  LOOP
    RAISE NOTICE 'INDEX %.%', schema_name, r.indexname;
    EXECUTE 'ALTER INDEX ' || schema_name || '.' || r.indexname || ' OWNER TO temboard;';
  END LOOP;

  FOR r IN SELECT
      n.nspname,
      t.typname
    FROM pg_catalog.pg_type t
      LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
      AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
      AND n.nspname = schema_name
    ORDER BY 1, 2
  LOOP
    RAISE NOTICE 'TYPE %.%', schema_name, r.typname;
    EXECUTE 'ALTER TYPE ' || schema_name || '.' || r.typname || ' OWNER TO temboard;';
  END LOOP;

END;
$$ language plpgsql;

SELECT __reassign_schema('application');
SELECT __reassign_schema('monitoring');
SELECT __reassign_schema('statements');
DROP FUNCTION __reassign_schema(TEXT);
