import logging
import cStringIO
from datetime import datetime
from textwrap import dedent

import tornado.web
import tornado.escape

from temboardui.plugins.monitoring.model.orm import (
    Check,
    CheckState,
)
from temboardui.web import (
    HTTPError,
    jsonify,
)

from . import (
    blueprint,
    render_template,
)
from ..tools import get_request_ids, parse_start_end
from ..alerting import checks_info, check_state_detail, check_specs

logger = logging.getLogger(__name__)


def sql_json_query(request, query, *args):
    # Helper to query JSON output from PostgreSQL.

    cur = request.db_session.connection().connection.cursor()
    query = cur.mogrify(query, args)
    data_buffer = cStringIO.StringIO()
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    try:
        return tornado.escape.json_decode(data)
    except Exception as e:
        logger.error("Failed to parse JSON from Postgres: %s", e)
        logger.error("Postgres output is: %r", data)
        return []


@blueprint.instance_route(r"/alerting/alerts.json")
def alerts(request):
    host_id, instance_id = get_request_ids(request)

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

    # Tornado refuses to send lists as JSON. We must explicitly use jsonify.
    # Cf. https://github.com/tornadoweb/tornado/issues/1009
    return jsonify(sql_json_query(request, query, host_id, instance_id))


@blueprint.instance_route(r"/alerting")
def index(request):
    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        # Monitoring plugin doesn't require agent authentication since we
        # already have the data.
        # Don't fail if there's a session error (for example when the agent
        # has been restarted)
        agent_username = None

    return render_template(
        'alerting.checks.html',
        nav=True, role=request.current_user,
        instance=request.instance, agent_username=agent_username,
        plugin='alerting',  # we cheat here
    )


@blueprint.instance_route("/alerting/checks.json", methods=['GET', 'POST'])
def checks(request):
    host_id, instance_id = get_request_ids(request)
    if 'GET' == request.method:
        data = checks_info(request.db_session, host_id, instance_id)
        for datum in data:
            spec = check_specs[datum['name']]
            if 'value_type' in spec:
                datum['value_type'] = spec['value_type']
        return jsonify(data)
    else:
        post = tornado.escape.json_decode(request.body)
        if 'checks' not in post or type(post.get('checks')) is not list:
            raise HTTPError(400, "Post data not valid.")

        for row in post['checks']:
            if row.get('name') not in check_specs:
                raise HTTPError(404, "Unknown check '%s'" % row.get('name'))

        for row in post['checks']:
            # Find the check from its name
            check = request.db_session.query(Check).filter(
                        Check.name == unicode(row.get('name')),
                        Check.host_id == host_id,
                        Check.instance_id == instance_id).first()
            enabled_before = check.enabled

            if u'enabled' in row:
                enabled_after = bool(row.get(u'enabled'))
                check.enabled = enabled_after
                # detect any change from enabled to disabled
                is_getting_disabled = enabled_before and not enabled_after
            if u'warning' in row:
                warning = row.get(u'warning')
                if type(warning) not in (int, float):
                    raise HTTPError(400, "Post data not valid.")
                check.warning = warning
            if u'critical' in row:
                critical = row.get(u'critical')
                if type(critical) not in (int, float):
                    raise HTTPError(400, "Post data not valid.")
                check.critical = critical
            if u'description' in row:
                check.description = row.get(u'description')

            request.db_session.merge(check)

            if is_getting_disabled:
                cs = request.db_session.query(CheckState).filter(
                    CheckState.check_id == check.check_id,
                )
                for i in cs:
                    i.state = unicode('UNDEF')
                    request.db_session.merge(i)
                    request.db_session.execute(
                        "SELECT monitoring.append_state_changes(:d, :i,"
                        ":s, :k, :v, :w, :c)",
                        {'d': datetime.utcnow(), 'i': check.check_id,
                         's': 'UNDEF', 'k': i.key, 'v': None,
                         'w': check.warning, 'c': check.critical})

        request.db_session.commit()

        return {}


@blueprint.instance_route(r"/alerting/([a-z\-_.0-9]{1,64})")
def check(request, name):
    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        # Monitoring plugin doesn't require agent authentication since we
        # already have the data.
        # Don't fail if there's a session error (for example when the agent
        # has been restarted)
        agent_username = None

    host_id, instance_id = get_request_ids(request)
    query = dedent("""\
    SELECT *
    FROM monitoring.checks
    WHERE host_id = :host_id
      AND instance_id = :instance_id
      AND name = :check_name
    """)
    res = request.db_session.execute(query, dict(
        host_id=host_id,
        instance_id=instance_id,
        check_name=name,
    ))
    check = res.fetchone()
    spec = check_specs[name]

    return render_template(
        'alerting.check.html',
        nav=True, role=request.current_user,
        instance=request.instance, agent_username=agent_username,
        plugin='alerting',  # we cheat here
        check=check,
        value_type=spec.get('value_type'),
    )


@blueprint.instance_route(r"/alerting/check_changes/([a-z\-_.0-9]{1,64}).json")
def check_changes(request, name):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

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
    return jsonify(sql_json_query(
        request, query,
        host_id, instance_id, name, start, end,
    ))


@blueprint.instance_route(r"/alerting/state_changes/([a-z\-_.0-9]{1,64}).json")
def state_changes(request, name):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)
    key = request.handler.get_argument('key', default=None)
    if name not in check_specs:
        raise HTTPError(404, "Unknown check '%s'" % name)

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

    return jsonify(sql_json_query(
        request, query,
        host_id, instance_id, name, key, start, end,
    ))


@blueprint.instance_route(r"/alerting/states/([a-z\-_.0-9]{1,64}).json")
def states(request, name):
    host_id, instance_id = get_request_ids(request)
    if name not in check_specs:
        raise HTTPError(404, "Unknown check '%s'" % name)

    detail = check_state_detail(request.db_session, host_id, instance_id, name)
    for d in detail:
        spec = check_specs[name]
        if 'value_type' in spec:
            d['value_type'] = spec['value_type']

    return jsonify(detail)
