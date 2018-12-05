# `temboard` configuration

## The configuraton file

The configuration file `temboard.conf` is formated using INI format. Configuration parameters are distributed under sections:
  - `[temboard]`: this is the main section grouping core parameters;
  - `[repository]`: connexion parameters to the repository;
  - `[logging]`: how and where to log;

### `[temboard]`
  - `port`: port number that `temboard` will listen on. Default: `8888`;
  - `address`: IP v4 address that `temboard` will listen on. Default: `0.0.0.0` (all);
  - `ssl_cert_file`: Path to SSL certificate file (.pem). Default: `/etc/temboard/ssl/temboard_CHANGEME.pem`;
  - `ssl_key_file`: Path to SSL private key file. Default: `/etc/temboard/ssl/temboard_CHANGEME.key`;
  - `ssl_ca_cert_file `: File where to store each agent's SSL certificate. Default: `/etc/temboard/ssl/temboard_ca_certs_CHANGEME.pem`;
  - `cookie_secret`: Secret key used to crypt cookie content. Default: `SECRETKEYTOBECHANGED`;
  - `plugins`: Array of plugin name to load. Default: `["monitoring", "dashboard", "pgconf", "activity"]`;

### `[repository]`
  - `host`: Repository host name or address. Default: `localhost`;
  - `port`: Repository port number. Default: `5432`;
  - `user`: Connection user. Default: `temboard`;
  - `password`: User password. Default: `None`;
  - `dbname`: Database name. Default: `temboard`;

### `[logging]`
  - `method`: Method used to send the logs: `stderr`, `syslog` or `file`. Default: `syslog`;
  - `facility`: Syslog facility. Default: `local0`;
  - `destination`: Path to the log file. Default: `/dev/log`;
  - `level`: Log level, can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. Default: `INFO`.
