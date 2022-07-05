CREATE SCHEMA IF NOT EXISTS application;
CREATE TABLE IF NOT EXISTS application.schema_migration_log (
  version TEXT UNIQUE NOT NULL PRIMARY KEY,
  cdate TIMESTAMP DEFAULT NOW(),
	comment TEXT
);
