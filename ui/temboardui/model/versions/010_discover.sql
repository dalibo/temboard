ALTER TABLE "application"."instances"
ADD COLUMN "cdate" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
ADD COLUMN "discover" JSONB,
ADD COLUMN "discover_date" TIMESTAMP WITH TIME ZONE,
ADD COLUMN "discover_etag" TEXT;

UPDATE "application"."instances"
SET "discover" = json_build_object(
  'system', json_build_object(
	  'cpu_count', "cpu",
		'memory', "memory_size",
		'fqdn', "hostname"
  ),
	'postgres', json_build_object(
	  'version', "pg_version",
	  'version_summary', "pg_version_summary",
		'port', "pg_port",
		'data_directory', "pg_data"
	),
	'temboard', json_build_object()
);

ALTER TABLE "application"."instances"
DROP COLUMN "cpu",
DROP COLUMN "memory_size",
DROP COLUMN "pg_data",
DROP COLUMN "pg_version",
DROP COLUMN "pg_version_summary";
