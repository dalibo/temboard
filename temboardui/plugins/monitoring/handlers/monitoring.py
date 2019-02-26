import logging

from temboardui.web import (
    HTTPError,
    anonymous_allowed,
    csvify,
)

from . import blueprint, render_template
from ..chartdata import (
    get_availability,
    get_unavailability_csv,
    get_metric_data_csv,
)
from ..tools import (
    check_agent_key,
    check_host_key,
    get_instance_checks,
    get_host_id,
    get_instance_id,
    get_request_ids,
    insert_availability,
    insert_metrics,
    merge_agent_info,
    parse_start_end,
    populate_host_checks,
)
from ..alerting import check_specs


logger = logging.getLogger('temboardui.plugins.' + __name__)


def check_agent_request(request, hostname, instance):
    key = request.headers.get('X-Key')
    if not key:
        raise HTTPError(401, 'X-Key header missing')

    if instance['available']:
        check_agent_key(request.db_session,
                        hostname,
                        instance['data_directory'],
                        instance['port'],
                        key)
    else:
        # Case when PostgreSQL instance is not started.
        check_host_key(request.db_session, hostname, key)


def build_check_task_options(request, host_id, instance_id, checks):
    options = dict(
        host_id=host_id,
        instance_id=instance_id,
        data=list(),
    )

    # Populate data with preprocessed values
    for check in checks:
        spec = check_specs.get(check[0])
        if not spec:
            continue

        try:
            v = spec.get('preprocess')(request.json['data'])
        except Exception:
            logger.warning("Failed to preprocess alerting check '%s'"
                           % check[0])
            continue

        if not isinstance(v, dict):
            v = {'': v}

        for key, val in v.items():
            options['data'].append(dict(
                datetime=request.json['datetime'],
                name=check[0],
                key=key,
                value=val,
                warning=check[1],
                critical=check[2]))
    return options


@blueprint.instance_route("/monitoring/availability")
def availability(request):
    request.instance.check_active_plugin('monitoring')
    host_id, instance_id = get_request_ids(request)
    data = get_availability(request.db_session, host_id, instance_id)
    return {'available': data}


@blueprint.route(r"/(?:monitoring|supervision)/collector",
                 methods=['POST'], json=True)
@anonymous_allowed
def collector(request):
    data = request.json

    try:
        # Ignore legacy multi-instance.
        instance = data['instances'][0]
        hostinfo = data['hostinfo']
        hostname = hostinfo['hostname']
        port = instance['port']
        metrics_data = data['data']
        n_cpu = hostinfo['cpu_count']
        if 'max_connections' in instance:
            data['data']['max_connections'] = instance['max_connections']
    except (KeyError, IndexError) as e:
        logger.exception(str(e))
        raise HTTPError(409, "Not valid data")

    check_agent_request(request, hostname, instance)

    # Update the inventory
    host = merge_agent_info(request.db_session, hostinfo, instance)

    # Send the write SQL commands to the database because the metrics are
    # inserted with queries not the orm. Tables must be there.
    request.db_session.commit()

    insert_availability(
        request.db_session, host, data, logger, hostname, port)
    insert_metrics(
        request.db_session, host, metrics_data, logger, hostname, port)

    # ALERTING PART

    host_id = get_host_id(request.db_session, hostname)
    instance_id = get_instance_id(request.db_session, host_id, port)
    populate_host_checks(request.db_session, host_id, instance_id,
                         dict(n_cpu=n_cpu))
    request.db_session.commit()

    # Create new task for checking preprocessed values
    task_options = build_check_task_options(
        request, host_id, instance_id,
        get_instance_checks(request.db_session, instance_id),
    )
    request.handler.application.temboard_app.scheduler.schedule_task(
        'check_data_worker',
        options=task_options,
        expire=0,
    )

    return {'done': True}


@blueprint.instance_route("/monitoring")
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
        'index.html',
        nav=True, role=request.current_user, instance=request.instance,
        plugin='monitoring', agent_username=agent_username,
    )


@blueprint.instance_route("/monitoring/unavailability")
def unavailability(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)
    data = get_unavailability_csv(
        request.db_session, start, end, host_id, instance_id)
    return csvify(data)


@blueprint.instance_route(r'/monitoring/data/([a-z\-_.0-9]{1,64})$')
def data_metric(request, metric_name):
    key = request.handler.get_argument('key', default=None)
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)
    try:
        data = get_metric_data_csv(
            request.db_session, metric_name,
            start, end,
            host_id=host_id,
            instance_id=instance_id,
            key=key,
        )
    except IndexError:
        raise HTTPError(404, 'Unknown metric.')

    return csvify(data=data)
