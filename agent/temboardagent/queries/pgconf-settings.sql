SELECT
	category, "name",
	setting,
	current_setting("name") AS current_setting,
	unit,
	vartype,
	min_val, max_val, enumvals,
	context,
	short_desc || ' ' || coalesce(extra_desc, '') AS "desc",
	boot_val, reset_val,
	pending_restart
FROM pg_settings
ORDER BY 1, 2;
