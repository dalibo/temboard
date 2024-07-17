SELECT
	category, "s"."name",
	"s".setting,
	current_setting("name") AS current_setting,
	unit,
	vartype,
	min_val, max_val, enumvals,
	context,
	short_desc || ' ' || coalesce(extra_desc, '') AS "desc",
	boot_val, reset_val,
	pending_restart,
	COALESCE(json_agg(
		json_build_object(
			'file', f.sourcefile,
			'line', f.sourceline,
			'seqno', f.seqno,
			'setting', f.setting,
			'error', f.error,
			'applied', f.applied
		)
	) FILTER (WHERE f.sourcefile IS NOT NULL), '[]'::JSON) AS sources
FROM pg_settings AS "s"
LEFT OUTER JOIN pg_file_settings AS "f" USING("name")
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14
ORDER BY 1, 2;
