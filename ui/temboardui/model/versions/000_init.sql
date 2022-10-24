CREATE SCHEMA IF NOT EXISTS application;
CREATE TABLE IF NOT EXISTS application.schema_migration_log (
  version TEXT UNIQUE NOT NULL PRIMARY KEY,
	comment TEXT,
  cdate TIMESTAMP DEFAULT NOW()
);
