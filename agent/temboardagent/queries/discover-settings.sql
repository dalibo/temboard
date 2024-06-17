SELECT
  "name", "vartype", "unit", "setting"
FROM pg_catalog.pg_settings
WHERE "name" IN (
  'config_file'
  ,'cluster_name'
  ,'data_directory'
  ,'external_pid_file'
  ,'hba_file'
  ,'ident_file'
  ,'lc_collate'
  ,'lc_ctype'
  ,'listen_addresses'
  ,'max_connections'
  ,'port'
  ,'server_encoding'
  ,'syslog_ident'
  ,'unix_socket_directories'
) OR context = 'internal';
