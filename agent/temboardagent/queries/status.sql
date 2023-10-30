SELECT
  pg_is_in_recovery() AS is_standby,
	(
		SELECT setting
		FROM pg_settings
		WHERE name = 'primary_conninfo') AS primary_conninfo,
  (
    SELECT bool_or(pending_restart)
    FROM pg_settings
  ) AS pending_restart
;
