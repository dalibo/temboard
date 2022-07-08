from datetime import datetime
import time
import logging
import json

from bottle import Bottle, default_app, request, HTTPError

from ...toolkit import taskmanager
from ...toolkit.configuration import OptionSpec
from ...toolkit.validators import commalist
from ...tools import now, validate_parameters
from ...inventory import SysInfo
from ... import __version__ as __VERSION__
from ...postgres import Postgres

from . import db
from .inventory import host_info, instance_info
from .probes import (
    load_probes,
    probe_bgwriter,
    probe_blocks,
    probe_cpu,
    probe_db_size,
    probe_filesystems_size,
    probe_heap_bloat,
    probe_btree_bloat,
    probe_loadavg,
    probe_locks,
    probe_memory,
    probe_process,
    probe_replication_lag,
    probe_replication_connection,
    probe_sessions,
    probe_temp_files_size_delta,
    probe_tblspc_size,
    probe_wal_files,
    probe_xacts,
    run_probes,
)
from .output import remove_passwords

logger = logging.getLogger(__name__)
bottle = Bottle()
workers = taskmanager.WorkerSet()

T_TIMESTAMP_UTC = b'(^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$)'
T_LIMIT = b'(^[0-9]+$)'


@bottle.get('/probe/sessions')
def get_probe_sessions():
    app = default_app().temboard
    return api_run_probe(probe_sessions(app.config.monitoring), app.config)


@bottle.get('/probe/xacts')
def get_probe_xacts():
    app = default_app().temboard
    return api_run_probe(probe_xacts(app.config.monitoring), app.config)


@bottle.get('/probe/locks')
def get_probe_locks():
    app = default_app().temboard
    return api_run_probe(probe_locks(app.config.monitoring), app.config)


@bottle.get('/probe/blocks')
def get_probe_blocks():
    app = default_app().temboard
    return api_run_probe(probe_blocks(app.config.monitoring), app.config)


@bottle.get('/probe/bgwriter')
def get_probe_bgwriter():
    app = default_app().temboard
    return api_run_probe(probe_bgwriter(app.config.monitoring), app.config)


@bottle.get('/probe/db_size')
def get_probe_db_size():
    app = default_app().temboard
    return api_run_probe(probe_db_size(app.config.monitoring), app.config)


@bottle.get('/probe/tblspc_size')
def get_probe_tblspc_size():
    app = default_app().temboard
    return api_run_probe(probe_tblspc_size(app.config.monitoring), app.config)


@bottle.get('/probe/filesystems_size')
def get_probe_filesystems_size():
    app = default_app().temboard
    return api_run_probe(probe_filesystems_size(app.config.monitoring),
                         app.config)


@bottle.get('/probe/cpu')
def get_probe_cpu():
    app = default_app().temboard
    return api_run_probe(probe_cpu(app.config.monitoring), app.config)


@bottle.get('/probe/process')
def get_probe_process():
    app = default_app().temboard
    return api_run_probe(probe_process(app.config.monitoring), app.config)


@bottle.get('/probe/memory')
def get_probe_memory():
    app = default_app().temboard
    return api_run_probe(probe_memory(app.config.monitoring), app.config)


@bottle.get('/probe/loadavg')
def get_probe_loadavg():
    app = default_app().temboard
    return api_run_probe(probe_loadavg(app.config.monitoring), app.config)


@bottle.get('/probe/wal_files')
def get_probe_wal_files():
    app = default_app().temboard
    return api_run_probe(probe_wal_files(app.config.monitoring), app.config)


@bottle.get('/probe/replication_lag')
def get_probe_replication_lag():
    app = default_app().temboard
    return api_run_probe(probe_replication_lag(app.config.monitoring),
                         app.config)


@bottle.get('/probe/temp_files_size_delta')
def get_probe_temp_files_size_delta():
    app = default_app().temboard
    return api_run_probe(probe_temp_files_size_delta(app.config.monitoring),
                         app.config)


@bottle.get('/probe/replication_connection')
def get_probe_replication_connection():
    app = default_app().temboard
    return api_run_probe(probe_replication_connection(app.config.monitoring),
                         app.config)


@bottle.get('/probe/heap_bloat')
def get_probe_heap_bloat():
    app = default_app().temboard
    return api_run_probe(probe_heap_bloat(app.config.monitoring), app.config)


@bottle.get('/probe/btree_bloat')
def get_probe_btree_bloat():
    app = default_app().temboard
    return api_run_probe(probe_btree_bloat(app.config.monitoring), app.config)


def api_run_probe(probe_instance, config):
    """
    Run a probe instance.
    """
    # Validate connection information from the config, and ensure
    # the instance is available
    conninfo = dict(
        host=config.postgresql.host,
        port=config.postgresql.port,
        user=config.postgresql.user,
        database=config.postgresql.dbname,
        password=config.postgresql.password,
        dbnames=config.monitoring.dbnames,
        instance=config.postgresql.instance,
    )
    postgres = Postgres(**conninfo)
    sysinfo = SysInfo()
    hostname = sysinfo.hostname(config.temboard.hostname)
    with postgres.dbpool() as pool:
        instance = instance_info(pool, conninfo, hostname)
        # Set home path
        probe_instance.set_home(config.temboard.home)
        # Gather the data from probes
        return run_probes([probe_instance], pool, [instance], delta=False)


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

    return [
        json.loads(metric[1]) for metric in db.get_metrics(
            app.config.temboard.home,
            'monitoring.db',
            start_timestamp=start_timestamp,
            limit=limit
        )
    ]


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
    conninfo = dict(
        host=config.postgresql.host,
        port=config.postgresql.port,
        user=config.postgresql.user,
        database=config.postgresql.dbname,
        password=config.postgresql.password,
        dbnames=config.monitoring.dbnames,
        instance=config.postgresql.instance,
    )

    logger.info("Gathering host information.")
    system_info = host_info(config.temboard.hostname)
    logger.info("Load the probes to run.")
    probes = load_probes(
        config.monitoring,
        config.temboard.home
    )

    with Postgres(**conninfo).dbpool() as pool:
        instance = instance_info(pool, conninfo, system_info['hostname'])
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
    for k, v in data.items():
        for vv in v:
            record = dict()
            for kkk, vvv in vv.items():
                if hasattr(vvv, 'isoformat'):
                    vvv = vvv.isoformat(sep='T')
                if kkk in ('datetime', 'port', 'cpu', 'measure_interval'):
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
