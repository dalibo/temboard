SELECT
version() AS version,
(SELECT split_part(version(), ' ', 1) || ' ' || setting FROM pg_catalog.pg_settings WHERE name = 'server_version') AS version_summary,
(SELECT setting::BIGINT FROM pg_catalog.pg_settings WHERE name = 'server_version_num') AS version_num
;
