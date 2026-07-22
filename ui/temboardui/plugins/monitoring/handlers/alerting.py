import io
import logging
from datetime import datetime
from textwrap import dedent


from temboardui.plugins.monitoring.model.orm import Check, CheckState

from ..alerting import check_specs, check_state_detail, checks_info
from ..tools import get_request_ids, parse_start_end
from ....web.flask import instance_routes
from flask import abort, current_app, g, json, jsonify, render_template, request

logger = logging.getLogger(__name__)


def sql_json_query(request, query, *args):
    # Helper to query JSON output from PostgreSQL.

    cur = g.db_session.connection().connection.cursor()
    query = cur.mogrify(query, args)
    data_buffer = io.StringIO()
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    try:
        return json.loads(data)
    except Exception as e:
        logger.error("Failed to parse JSON from Postgres: %s", e)
        logger.error("Postgres output is: %r", data)
        return []


@instance_routes.route(r"/alerting/alerts.json")
def alerting_alerts():
    try:
        host_id, instance_id = get_request_ids()
    except NameError as e:
        logger.info("Unknown host or no data: %s." % e)
        return jsonify([])

    query = dedent("""\
    COPY (
        SELECT array_to_json(coalesce(array_agg(x), '{}'))
        FROM (
            SELECT json_build_object('description', c.description, 'name', c.name, 'key', sc.key, 'state', sc.state, 'datetime', sc.datetime, 'value', sc.value, 'warning', sc.warning, 'critical', sc.critical) as x
            FROM monitoring.state_changes sc JOIN monitoring.checks c ON (sc.check_id = c.check_id)
            WHERE c.host_id = %s
              AND c.instance_id = %s
              AND (sc.state = 'WARNING' OR sc.state = 'CRITICAL')
            ORDER BY sc.datetime desc
            LIMIT 20
        ) as tab
    ) TO STDOUT
    """)  # noqa

    return sql_json_query(request, query, host_id, instance_id)


@instance_routes.route(r"/alerting")
def alerting_index():
    current_app.instance.fetch_status()
    return render_template(
        "monitoring/alerting.checks.html",
        role=g.current_user,
        instance=g.instance,
        plugin="alerting",  # we cheat here
    )


@instance_routes.route("/alerting/checks.json", methods=["GET", "POST"])
def alerting_checks():
    try:
        host_id, instance_id = get_request_ids()
    except NameError as e:
        logger.info("Unknown host or no data: %s." % e)
        return jsonify([])

    if "GET" == request.method:
        data = checks_info(g.db_session, host_id, instance_id)
        for datum in data:
            spec = check_specs[datum["name"]]
            if "value_type" in spec:
                datum["value_type"] = spec["value_type"]
        return jsonify(data)
    else:
        post = request.json
        if "checks" not in post or type(post.get("checks")) is not list:
            raise abort(400, "Post data not valid.")

        for row in post["checks"]:
            if row.get("name") not in check_specs:
                raise abort(400, "Unknown check '%s'" % row.get("name"))

        for row in post["checks"]:
            # Find the check from its name
            check = (
                g.db_session.query(Check)
                .filter(
                    Check.name == str(row.get("name")),
                    Check.host_id == host_id,
                    Check.instance_id == instance_id,
                )
                .first()
            )
            enabled_before = check.enabled
            is_getting_disabled = False
            if "enabled" in row:
                enabled_after = bool(row.get("enabled"))
                check.enabled = enabled_after
                # detect any change from enabled to disabled
                is_getting_disabled = enabled_before and not enabled_after
            if "warning" in row:
                warning = row.get("warning")
                if type(warning) not in (int, float):
                    raise abort(400, "Post data not valid.")
                check.warning = warning
            if "critical" in row:
                critical = row.get("critical")
                if type(critical) not in (int, float):
                    raise abort(400, "Post data not valid.")
                check.critical = critical
            if "description" in row:
                check.description = row.get("description")

            g.db_session.merge(check)

            if is_getting_disabled:
                cs = g.db_session.query(CheckState).filter(
                    CheckState.check_id == check.check_id
                )
                for i in cs:
                    i.state = "UNDEF"
                    g.db_session.merge(i)
                    g.db_session.execute(
                        "SELECT monitoring.append_state_changes(:d, :i,"
                        ":s, :k, :v, :w, :c)",
                        {
                            "d": datetime.utcnow(),
                            "i": check.check_id,
                            "s": "UNDEF",
                            "k": i.key,
                            "v": None,
                            "w": check.warning,
                            "c": check.critical,
                        },
                    )

        g.db_session.commit()

        return {}


@instance_routes.route(r"/alerting/<name>")
def alerting_check(name):
    host_id, instance_id = get_request_ids()
    query = dedent("""\
    SELECT *
    FROM monitoring.checks
    WHERE host_id = :host_id
      AND instance_id = :instance_id
      AND name = :check_name
    """)
    res = g.db_session.execute(
        query, dict(host_id=host_id, instance_id=instance_id, check_name=name)
    )
    check = res.fetchone()
    spec = check_specs[name]
    current_app.instance.fetch_status()
    return render_template(
        "monitoring/alerting.check.html",
        role=g.current_user,
        instance=g.instance,
        plugin="alerting",  # we cheat here
        check=check,
        value_type=spec.get("value_type"),
    )


@instance_routes.route(r"/alerting/check_changes/<name>.json")
def alerting_check_changes(name):
    host_id, instance_id = get_request_ids()
    start, end = parse_start_end()

    query = dedent("""\
    COPY (
        SELECT array_to_json(coalesce(array_agg(json_build_object(
            'datetime', f.datetime,
            'enabled', f.enabled,
            'warning', f.warning,
            'critical', f.critical,
            'description', f.description
        )), '{}')) FROM monitoring.get_check_changes(%s, %s, %s, %s, %s) f
    ) TO STDOUT
    """)
    return jsonify(
        sql_json_query(request, query, host_id, instance_id, name, start, end)
    )


@instance_routes.route(r"/alerting/state_changes/<name>.json")
def alerting_state_changes(name):
    host_id, instance_id = get_request_ids()
    start, end = parse_start_end()
    key = request.args.get("key")
    if name not in check_specs:
        raise abort(400, "Unknown check '%s'" % name)

    query = dedent("""\
    COPY (
        SELECT array_to_json(coalesce(array_agg(json_build_object(
            'datetime', f.datetime,
            'state', f.state,
            'value', f.value,
            'warning', f.warning,
            'critical', f.critical
        )), '{}')) FROM monitoring.get_state_changes(%s, %s, %s, %s, %s, %s) f
    ) TO STDOUT
    """)

    return jsonify(
        sql_json_query(request, query, host_id, instance_id, name, key, start, end)
    )


@instance_routes.route(r"/alerting/states/<name>.json")
def alerting_states(name):
    host_id, instance_id = get_request_ids()
    if name not in check_specs:
        raise abort(400, "Unknown check '%s'" % name)

    detail = check_state_detail(g.db_session, host_id, instance_id, name)
    for d in detail:
        spec = check_specs[name]
        if "value_type" in spec:
            d["value_type"] = spec["value_type"]

    return jsonify(detail)
