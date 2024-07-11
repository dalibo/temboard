import logging
import re
from collections import namedtuple
from textwrap import dedent

from bottle import HTTPError, request

from ...errors import NotificationError
from ...notification import Notification, NotificationMgmt
from ...postgres import pg_escape

logger = logging.getLogger(__package__)


class FileSetting(
    namedtuple("FileSetting", ["name", "setting", "sourcefile", "sourceline"])
):
    pass


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


def preformat(setting, type):
    if setting.startswith("'") and setting.endswith("'"):
        setting = setting[1:-1]
    if type == "bool":
        if setting == "true":
            setting = "on"
        elif setting == "false":
            setting = "off"
    return setting


def format_setting(setting, type, unit=None):
    if not setting:
        return
    if type == "integer":
        setting = int(human_to_number(setting, unit))
    elif type == "real":
        setting = float(setting)
    return setting


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


def human_to_number(h_value, h_unit=None, h_type=int):
    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "YB", "ZB"]
    re_unit = re.compile(r"([0-9.]+)\s*([KMGBTPEYZ]?B)$", re.IGNORECASE)
    m_value = re_unit.match(str(h_value))
    factor = 1
    if h_unit:
        m_unit = re_unit.match(str(h_unit))
        if m_unit:
            factor = int(m_unit.group(1))
            h_unit = str(m_unit.group(2))

    if m_value:
        p_num = m_value.group(1)
        p_unit = m_value.group(2)
        m = 0
        for u in units:
            if h_unit and h_unit.lower() == u.lower():
                m = 0
            if u.lower() == p_unit.lower():
                return (int(p_num) * (1024**m)) / factor
            else:
                m += 1

    # Valid time units are ms (milliseconds), s (seconds), min (minutes),
    # h (hours), and d (days
    re_unit = re.compile(r"([0-9.]+)\s*(us|ms|s|min|h|d)$")
    m_unit = re_unit.match(str(h_value))
    if h_unit == "ms":
        mult = {
            "us": 0.001,
            "ms": 1,
            "s": 1000,
            "min": 60000,
            "h": 3600000,
            "d": 86400000,
        }
    elif h_unit == "s":
        mult = {"ms": -1000, "s": 1, "min": 60, "h": 3600, "d": 86400}
    elif h_unit == "min":
        mult = {"ms": -60000, "s": -60, "min": 1, "h": 60, "d": 1440}
    elif h_unit == "h":
        mult = {"ms": -3600000, "s": -3600, "min": -60, "h": 1, "d": 24}
    elif h_unit == "d":
        mult = {"ms": -86400000, "s": -86400, "min": -1440, "h": -24, "d": 1}
    else:
        mult = {"ms": 1, "s": 1, "min": 1, "h": 1, "d": 1}

    if m_unit:
        p_num = m_unit.group(1)
        p_unit = m_unit.group(2)
        if mult[p_unit] > 0:
            return h_type(p_num) * mult[p_unit]
        else:
            return h_type(p_num) / abs(mult[p_unit])

    return h_value


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


def post_settings(app, conn, current, update):
    ret = {"settings": []}
    do_not_check_names = ["unix_socket_permissions", "log_file_mode"]
    for setting in update:
        if "name" not in setting or "setting" not in setting:
            raise HTTPError(406, "setting item malformed.")
        checked = False
        try:
            for pg_config_category in current:
                for item in pg_config_category["rows"]:
                    if item["name"] == setting["name"]:
                        if item["name"] in do_not_check_names:
                            checked = True
                            raise Exception()
                        if item["vartype"] == "integer":
                            # Integers handling.
                            if (
                                item["min_val"]
                                and item["unit"]
                                and (
                                    int(
                                        human_to_number(
                                            setting["setting"], item["unit"]
                                        )
                                    )
                                    < int(item["min_val"])
                                )
                            ):
                                raise HTTPError(
                                    406, "%s: Invalid setting." % (item["name"])
                                )
                            if (
                                item["max_val"]
                                and item["unit"]
                                and (
                                    int(
                                        human_to_number(
                                            setting["setting"], item["unit"]
                                        )
                                    )
                                    > int(item["max_val"])
                                )
                            ):
                                raise HTTPError(
                                    406, "%s: Invalid setting." % (item["name"])
                                )
                            setting["setting"] = pg_escape(setting["setting"])
                            if (
                                setting["setting"].startswith("'")
                                and setting["setting"].endswith("'")
                            ) or (
                                setting["setting"].startswith('"')
                                and setting["setting"].endswith('"')
                            ):
                                setting["setting"] = setting["setting"][1:-1]
                            if setting["setting"] == "":
                                setting["setting"] = None
                            checked = True
                        if item["vartype"] == "real":
                            setting["setting"] = human_to_number(
                                setting["setting"], item["unit"], float
                            )
                            # Real handling.
                            if item["min_val"] and (
                                float(setting["setting"]) < float(item["min_val"])
                            ):
                                raise HTTPError(
                                    406, "%s: Invalid setting." % (item["name"])
                                )
                            if item["max_val"] and (
                                float(setting["setting"]) > float(item["max_val"])
                            ):
                                raise HTTPError(
                                    406, "%s: Invalid setting." % (item["name"])
                                )
                            checked = True
                        if item["vartype"] == "bool":
                            # Boolean handling.
                            if setting["setting"].lower() not in ["on", "off"]:
                                raise HTTPError(
                                    406,
                                    "Invalid setting: %s."
                                    % (setting["setting"].lower()),
                                )
                            checked = True
                        if item["vartype"] == "enum":
                            # Enum handling.
                            if len(item["enumvals"]) > 0:
                                enumvals = [
                                    re.sub(r"^[\"\'](.+)[\"\ ']$", r"\1", enumval)
                                    for enumval in item["enumvals"][1:-1].split(",")
                                ]
                                if (
                                    setting["setting"].startswith("'")
                                    and setting["setting"].endswith("'")
                                ) or (
                                    setting["setting"].startswith('"')
                                    and setting["setting"].endswith('"')
                                ):
                                    setting["setting"] = setting["setting"][1:-1]
                                if setting["setting"] not in enumvals:
                                    raise HTTPError(
                                        406,
                                        "Invalid setting: %s." % (setting["setting"]),
                                    )
                                checked = True
                        if item["vartype"] == "string":
                            # String handling.
                            # setting must be escaped.
                            setting["setting"] = pg_escape(str(setting["setting"]))
                            if (
                                setting["setting"].startswith("'")
                                and setting["setting"].endswith("'")
                            ) or (
                                setting["setting"].startswith('"')
                                and setting["setting"].endswith('"')
                            ):
                                setting["setting"] = setting["setting"][1:-1]
                            if setting["setting"] == "":
                                setting["setting"] = None
                            checked = True
                        raise Exception()
        except HTTPError:
            raise
        except Exception:
            pass
        if not checked:
            raise HTTPError(406, "Parameter %s can't be checked." % (setting["name"]))
        if "force" not in setting:
            setting["force"] = "false"
        if (
            (item["vartype"] == "integer" and setting["setting"] != item["setting_raw"])
            or (
                item["vartype"] == "real"
                and float(setting["setting"]) != float(item["setting"])
            )
            or (
                item["vartype"] not in ["integer", "real"]
                and setting["setting"] != item["setting"]
            )
        ) or (setting["force"] == "true"):
            # At this point, all incoming parameters have been checked.
            if setting["setting"]:
                query = "ALTER SYSTEM SET {} TO '{}'".format(
                    setting["name"], setting["setting"]
                )
            else:
                query = "ALTER SYSTEM RESET %s;" % (setting["name"])

            logger.debug(query)

            # Push a notification on setting change.
            try:
                NotificationMgmt.push(
                    app.config,
                    Notification(
                        username=request.username,
                        message="Setting '{}' changed: '{}' -> '{}'".format(
                            item["name"], item["setting_raw"], setting["setting"]
                        ),
                    ),
                )
            except NotificationError as e:
                logger.error(e.message)

            try:
                conn.execute(query)
            except Exception as e:
                raise HTTPError(408, "{}: {}".format(setting["name"], e))
            ret["settings"].append(
                {
                    "name": item["name"],
                    "setting": setting["setting"],
                    "previous_setting": item["setting_raw"],
                    "restart": True
                    if item["context"] in ["internal", "postmaster"]
                    else False,
                }
            )
    # Reload PG configuration.
    conn.execute("SELECT pg_reload_conf()")
    # Push a notification.
    try:
        NotificationMgmt.push(
            app.config,
            Notification(username=request.username, message="PostgreSQL reload"),
        )
    except NotificationError as e:
        logger.error(e.message)

    return ret
