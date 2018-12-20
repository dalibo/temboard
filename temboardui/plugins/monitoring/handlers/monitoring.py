import logging
from dateutil import parser as dt_parser

import tornado.web
import tornado.escape

from temboardui.handlers.base import CsvHandler
from temboardui.errors import TemboardUIError
from temboardui.async import (
    run_background,
    CSVAsyncResult,
)
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
    get_host_checks,
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
        dbconf=dict(request.config.repository),
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
        except Exception as e:
            logger.exception("Failed to preprocess '%s': %s", check[0], e)
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
    hostname = data['hostinfo']['hostname']
    # Ignore legacy multi-instance.
    instance = data['instances'][0]

    check_agent_request(request, hostname, instance)

    # Update the inventory
    host = merge_agent_info(request.db_session,
                            data['hostinfo'],
                            data['instances'])

    # Send the write SQL commands to the database because the metrics are
    # inserted with queries not the orm. Tables must be there.
    request.db_session.commit()

    insert_availability(
        request.db_session, host, data, logger, hostname, instance['port'])
    insert_metrics(
        request.db_session, host, data['data'], logger, hostname,
        instance['port'])

    # ALERTING PART

    host_id = get_host_id(request.db_session, hostname)
    instance_id = get_instance_id(request.db_session,
                                  host_id, instance['port'])
    populate_host_checks(request.db_session, host_id, instance_id,
                         dict(n_cpu=data['hostinfo']['cpu_count']))
    request.db_session.commit()

    if 'max_connections' in instance:
        data['data']['max_connections'] = instance['max_connections']

    # Create new task for checking preprocessed values
    task_options = build_check_task_options(
        request, host_id, instance_id,
        get_host_checks(request.db_session, host_id),
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


class MonitoringCsvHandler(CsvHandler):

    def build(self, agent_address, agent_port):
        self.setUp(agent_address, agent_port)
        self.check_active_plugin('monitoring')

        # Find host_id & instance_id
        host_id = get_host_id(self.db_session, self.instance.hostname)
        instance_id = get_instance_id(self.db_session, host_id,
                                      self.instance.pg_port)

        start = self.get_argument('start', default=None)
        end = self.get_argument('end', default=None)
        start_time = None
        end_time = None
        if start:
            try:
                start_time = dt_parser.parse(start)
            except ValueError:
                raise TemboardUIError(406, 'Datetime not valid.')
        if end:
            try:
                end_time = dt_parser.parse(end)
            except ValueError:
                raise TemboardUIError(406, 'Datetime not valid.')
        return host_id, instance_id, start_time, end_time


class MonitoringUnavailabilityHandler(MonitoringCsvHandler):

    @CsvHandler.catch_errors
    def get_unavailability(self, agent_address, agent_port):
        host_id, instance_id, start_time, end_time = self.build(
            agent_address, agent_port)
        try:
            # Try to load data from the repository
            data = get_unavailability_csv(self.db_session,
                                          start_time, end_time,
                                          host_id=host_id,
                                          instance_id=instance_id)
        except IndexError as e:
            logger.exception(str(e))
            raise TemboardUIError(404, 'Unknown metric.')

        return CSVAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_unavailability, self.async_callback,
                       (agent_address, agent_port))


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
