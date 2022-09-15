from datetime import datetime
import time
import logging
import json

from bottle import Bottle, default_app, request, HTTPError, response

from ...toolkit import taskmanager
from ...toolkit.configuration import OptionSpec
from ...toolkit.validators import commalist
from ...tools import now, validate_parameters
from ... import __version__ as __VERSION__

from . import db
from .inventory import host_info, instance_info
from .probes import (
    load_probes,
    run_probes,
)
from .output import remove_passwords
from .openmetrics import (
    format_open_metrics_lines,
    generate_samples,
)

logger = logging.getLogger(__name__)
bottle = Bottle()
workers = taskmanager.WorkerSet()

T_TIMESTAMP_UTC = b'(^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$)'
T_LIMIT = b'(^[0-9]+$)'


@bottle.get('/metrics')
def get_metrics():
    app = default_app().temboard
    response.headers['Content-Type'] = 'text/plain; version=0.0.4'

    rows = db.get_metrics(app.config.temboard.home, 'monitoring.db')
    if not rows:
        return '# EOF\n'
    (_, data), = rows
    data = json.loads(data)
    db.use_current_for_delta_metrics(data)
    lines = format_open_metrics_lines(generate_samples(data))
    return '\n'.join(lines)


@bottle.get('/history')
def get_monitoring():
    """Monitoring root API aims to query metrics history.
    Data are sorted by collect timestamp, in ascending order. By default, only
    the most fresh record set is returned. The query parameter 'start' can be
    used as lower bound and must be expressed as a UTC timestamp formatted
    using ISO8601 norm with a terminal 'Z' character. To limit the number of
    returned records to N, the query parameter 'limit' can be used and set to
    N. 'limit' default value is 50, meaning that the maximum number of record
    set this API returns by default is 50.
    """

    # Default values
    start_timestamp = None
    limit = 50

    app = default_app().temboard

    if 'start' in request.query:
        # Validate start parameter
        validate_parameters(request.query, [
            ('start', T_TIMESTAMP_UTC, False),
        ])
        # Convert it to epoch
        try:
            start_timestamp = (
                datetime.strptime(
                    request.query['start'], "%Y-%m-%dT%H:%M:%SZ"
                ) - datetime(1970, 1, 1)
            ).total_seconds()
        except ValueError:
            raise HTTPError(406, "Invalid timestamp")

    if 'limit' in request.query:
        # Validate limit parameter
        validate_parameters(request.query, [
            ('limit', T_LIMIT, False),
        ])
        limit = int(request.query['limit'])

    out = []
    h, n = app.config.temboard.home, 'monitoring.db',
    for _, metrics in db.get_metrics(h, n, limit, start_timestamp):
        metrics = json.loads(metrics)
        # Dropping current value, use /metrics to get them.
        db.drop_current_for_delta_metrics(metrics)
        out.append(metrics)
    response.set_header('X-TemBoard-Discover-ETag', app.discover.etag)
    return out


@bottle.get('/config')
def get_config():
    """Returns monitoring plugin configuration.
    """
    app = default_app().temboard
    return dict(
        dbnames=app.config.monitoring.dbnames,
        scheduler_interval=app.config.monitoring.scheduler_interval,
    )


@workers.register(pool_size=1)
def monitoring_collector_worker(app):
    """
    Run probes and push collected metrics in a queue.
    """
    logger.info("Starting monitoring collector.")
    config = app.config
    logger.info("Gathering host information.")
    discover = app.discover.ensure_latest()
    system_info = host_info(discover)
    logger.info("Load the probes to run.")
    probes = load_probes(
        config.monitoring,
        config.temboard.home
    )

    with app.postgres.dbpool() as pool:
        instance = instance_info(pool, app.config.monitoring.dbnames, discover)
        data = run_probes(probes, pool, [instance])

    # Prepare and send output
    output = dict(
        datetime=now(),
        hostinfo=system_info,
        instances=remove_passwords([instance]),
        data=data,
        version=__VERSION__,
    )
    logger.info("Add data to metrics table.")
    db.add_metric(
        config.temboard.home,
        'monitoring.db',
        time.time(),
        output
    )

    logger.info("Collect done.")

    try:
        logger.debug("temboard_agent_version=%s", __VERSION__)
        logger.debug("hostinfo=%s", system_info)
        for record in iter_metrics_for_logfmt(data):
            # up=1 is a marker to grep logfmt lines
            logger.debug(
                "up=1 %s",
                " ".join('%s=%s' % i for i in record.items()),
            )
    except Exception:
        logger.exception("Failed to log metrics.")


def iter_metrics_for_logfmt(data):
    # Generates a flat sequence of record dict containing key value for logfmt
    # printing. See dev/perfui/ in temboard project to analyze such data.
    blacklist = ('current', 'datetime', 'port', 'cpu', 'measure_interval')
    for k, v in data.items():
        for vv in v:
            record = dict()
            for kkk, vvv in vv.items():
                if hasattr(vvv, 'isoformat'):
                    vvv = vvv.isoformat(sep='T')
                if kkk in blacklist:
                    continue
                if kkk in ('dbname', 'spcname') or k in ('loadavg', 'memory'):
                    record[kkk] = vvv
                elif k.endswith('_size') and kkk == 'size':
                    record[k] = vvv
                elif k == 'lag':
                    record[k] = vvv
                else:
                    record['%s_%s' % (k, kkk)] = vvv
            yield record


class MonitoringPlugin:
    PG_MIN_VERSION = (90400, 9.4)
    s = 'monitoring'
    option_specs = [
        OptionSpec(s, 'dbnames', default='*', validator=commalist),
        OptionSpec(s, 'scheduler_interval', default=60, validator=int),
        OptionSpec(s, 'probes', default='*', validator=commalist),
    ]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def load(self):
        default_app().mount('/monitoring', bottle)
        self.app.worker_pool.add(workers)
        logger.debug(
            "Schedule metric collect every %s seconds.",
            self.app.config.monitoring.scheduler_interval,
        )
        workers.schedule(
            id='monitoring_collector',
            redo_interval=self.app.config.monitoring.scheduler_interval,
        )(monitoring_collector_worker)
        self.app.scheduler.add(workers)

    def unload(self):
        self.app.scheduler.remove(workers)
        self.app.worker_pool.remove(workers)
        self.app.config.remove_specs(self.option_specs)
