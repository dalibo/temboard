SELECT
  "name", "vartype", "unit", "setting"
FROM pg_catalog.pg_settings
WHERE "name" IN (
  'block_size'
  ,'config_file'
  ,'cluster_name'
  ,'data_checksums'
  ,'data_directory'
  ,'hba_file'
  ,'ident_file'
  ,'lc_collate'
  ,'lc_ctype'
  ,'listen_addresses'
  ,'max_connections'
  ,'port'
  ,'segment_size'
  ,'server_encoding'
  ,'syslog_ident'
  ,'unix_socket_directories'
  ,'wal_block_size'
  ,'wal_segment_size'
)
