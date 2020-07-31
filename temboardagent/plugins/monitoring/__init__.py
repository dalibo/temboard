from datetime import datetime
import time
import logging
import json

from temboardagent.toolkit import taskmanager
from temboardagent.routing import RouteSet
from temboardagent.toolkit.configuration import OptionSpec
from temboardagent.toolkit.validators import commalist
from temboardagent.tools import now, validate_parameters
from temboardagent.inventory import SysInfo
from temboardagent import __version__ as __VERSION__
from temboardagent.errors import HTTPError as TemboardHTTPError

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
workers = taskmanager.WorkerSet()
routes = RouteSet(prefix=b'/monitoring')

T_TIMESTAMP_UTC = b'(^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$)'
T_LIMIT = b'(^[0-9]+$)'


@routes.get(b'/probe/sessions', check_key=True)
def get_probe_sessions(http_context, app):
    return api_run_probe(probe_sessions(app.config.monitoring), app.config)


@routes.get(b'/probe/xacts', check_key=True)
def get_probe_xacts(http_context, app):
    return api_run_probe(probe_xacts(app.config.monitoring), app.config)


@routes.get(b'/probe/locks', check_key=True)
def get_probe_locks(http_context, app):
    return api_run_probe(probe_locks(app.config.monitoring), app.config)


@routes.get(b'/probe/blocks', check_key=True)
def get_probe_blocks(http_context, app):
    return api_run_probe(probe_blocks(app.config.monitoring), app.config)


@routes.get(b'/probe/bgwriter', check_key=True)
def get_probe_bgwriter(http_context, app):
    return api_run_probe(probe_bgwriter(app.config.monitoring), app.config)


@routes.get(b'/probe/db_size', check_key=True)
def get_probe_db_size(http_context, app):
    return api_run_probe(probe_db_size(app.config.monitoring), app.config)


@routes.get(b'/probe/tblspc_size', check_key=True)
def get_probe_tblspc_size(http_context, app):
    return api_run_probe(probe_tblspc_size(app.config.monitoring), app.config)


@routes.get(b'/probe/filesystems_size', check_key=True)
def get_probe_filesystems_size(http_context, app):
    return api_run_probe(probe_filesystems_size(app.config.monitoring),
                         app.config)


@routes.get(b'/probe/cpu', check_key=True)
def get_probe_cpu(http_context, app):
    return api_run_probe(probe_cpu(app.config.monitoring), app.config)


@routes.get(b'/probe/process', check_key=True)
def get_probe_process(http_context, app):
    return api_run_probe(probe_process(app.config.monitoring), app.config)


@routes.get(b'/probe/memory', check_key=True)
def get_probe_memory(http_context, app):
    return api_run_probe(probe_memory(app.config.monitoring), app.config)


@routes.get(b'/probe/loadavg', check_key=True)
def get_probe_loadavg(http_context, app):
    return api_run_probe(probe_loadavg(app.config.monitoring), app.config)


@routes.get(b'/probe/wal_files', check_key=True)
def get_probe_wal_files(http_context, app):
    return api_run_probe(probe_wal_files(app.config.monitoring), app.config)


@routes.get(b'/probe/replication_lag', check_key=True)
def get_probe_replication_lag(http_context, app):
    return api_run_probe(probe_replication_lag(app.config.monitoring),
                         app.config)


@routes.get(b'/probe/temp_files_size_delta', check_key=True)
def get_probe_temp_files_size_delta(http_context, app):
    return api_run_probe(probe_temp_files_size_delta(app.config.monitoring),
                         app.config)


@routes.get(b'/probe/replication_connection', check_key=True)
def get_probe_replication_connection(http_context, app):
    return api_run_probe(probe_replication_connection(app.config.monitoring),
                         app.config)


@routes.get(b'/probe/heap_bloat', check_key=True)
def get_probe_heap_bloat(http_context, app):
    return api_run_probe(probe_heap_bloat(app.config.monitoring), app.config)


@routes.get(b'/probe/btree_bloat', check_key=True)
def get_probe_btree_bloat(http_context, app):
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
    sysinfo = SysInfo()
    hostname = sysinfo.hostname(config.temboard.hostname)
    instance = instance_info(conninfo, hostname)
    # Set home path
    probe_instance.set_home(config.temboard.home)
    # Gather the data from probes
    return run_probes([probe_instance], [instance], delta=False)


@routes.get(b'/history', check_key=True)
def get_monitoring(http_context, app):
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

    if 'start' in http_context['query']:
        # Validate start parameter
        validate_parameters(http_context['query'], [
            ('start', T_TIMESTAMP_UTC, True),
        ])
        # Convert it to epoch
        try:
            start_timestamp = (
                datetime.strptime(
                    http_context['query']['start'][0], "%Y-%m-%dT%H:%M:%SZ"
                ) - datetime(1970, 1, 1)
            ).total_seconds()
        except ValueError:
            raise TemboardHTTPError(406, "Invalid timestamp")

    if 'limit' in http_context['query']:
        # Validate limit parameter
        validate_parameters(http_context['query'], [
            ('limit', T_LIMIT, True),
        ])
        limit = int(http_context['query']['limit'][0])

    return [
        json.loads(metric[1]) for metric in db.get_metrics(
            app.config.temboard.home,
            'monitoring.db',
            start_timestamp=start_timestamp,
            limit=limit
        )
    ]


@routes.get(b'/config', check_key=True)
def get_config(http_context, app):
    """Returns monitoring plugin configuration.
    """
    return dict(
        dbnames=app.config.monitoring.dbnames,
        scheduler_interval=app.config.monitoring.scheduler_interval,
    )


@workers.register(pool_size=1)
def monitoring_collector_worker(app):
    """
    Run probes and push collected metrics in a queue.
    """
    logger.debug("Starting monitoring collector")
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

    system_info = host_info(config.temboard.hostname)
    # Load the probes to run
    probes = load_probes(
        config.monitoring,
        config.temboard.home
    )

    instance = instance_info(conninfo, system_info['hostname'])

    logger.debug("Running probes")
    # Gather the data from probes
    data = run_probes(probes, [instance])

    # Prepare and send output
    output = dict(
        datetime=now(),
        hostinfo=system_info,
        instances=remove_passwords([instance]),
        data=data,
        version=__VERSION__,
    )
    logger.debug(output)

    # Add data to metrics table
    db.add_metric(
        config.temboard.home,
        'monitoring.db',
        time.time(),
        output
    )

    logger.debug("Done")


class MonitoringPlugin(object):
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

    def bootstrap(self):
        db.bootstrap(self.app.config.temboard.home, 'monitoring.db')

    def load(self):
        self.app.router.add(routes)
        self.app.worker_pool.add(workers)
        workers.schedule(
            id='monitoring_collector',
            redo_interval=self.app.config.monitoring.scheduler_interval,
        )(monitoring_collector_worker)
        self.app.scheduler.add(workers)

    def unload(self):
        self.app.scheduler.remove(workers)
        self.app.worker_pool.remove(workers)
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.option_specs)
