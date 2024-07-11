from textwrap import dedent


def get_settings_categories(conn):
    return {
        "categories": [
            row["category"]
            for row in conn.query("""\
    SELECT DISTINCT(category) FROM pg_settings ORDER BY category
    """)
        ]
    }


def get_setting(conn, name):
    return conn.queryscalar("SELECT setting FROM pg_settings WHERE name = %s", (name,))


def get_settings(conn, category=None, search=None):
    where = ""
    if search:
        where = dedent("""\
        WHERE name ILIKE '%{0}%'
         OR short_desc ILIKE '%{0}%'
         OR extra_desc ILIKE '%{0}%'
        """).format(search)
    query = (
        dedent("""\
    SELECT
      name,
      setting,
      current_setting(name) AS current_setting,
      unit,
      vartype,
      min_val, max_val, enumvals,
      context, category,
      short_desc || ' ' || coalesce(extra_desc, '') AS desc,
      boot_val, reset_val,
      pending_restart
    FROM pg_settings
    %s
    ORDER BY category, name
    """)
        % where
    )

    ret = {}
    for row in conn.query(query):
        if category and category != row["category"]:
            continue

        rows = ret.setdefault(row["category"], [])
        enumvals = row["enumvals"]
        if enumvals is not None:
            # format enumvals as before switching from tpc to psycopg2
            enumvals = "{%s}" % ",".join(enumvals)
        rows.append(
            {
                "name": row["name"],
                "setting": row["setting"],
                "setting_raw": row["current_setting"],
                "unit": row["unit"],
                "vartype": row["vartype"],
                "min_val": row["min_val"],
                "max_val": row["max_val"],
                "boot_val": row["boot_val"],
                "reset_val": row["reset_val"],
                "enumvals": enumvals,
                "context": row["context"],
                "desc": row["desc"],
                "pending_restart": row["pending_restart"],
            }
        )

    return [{"category": k, "rows": v} for k, v in ret.items()]


def get_settings_status(conn):
    settings = get_settings(conn)
    pending_restart_changes = []
    pending_restart = False
    for category in settings:
        for row in category["rows"]:
            if row["pending_restart"]:
                pending_restart = True
                pending_restart_changes.append(row)
    return {
        "restart_pending": pending_restart,
        "restart_changes": pending_restart_changes,
    }
