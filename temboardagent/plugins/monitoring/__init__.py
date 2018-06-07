import time
import os
import logging
import json
try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

from temboardagent.toolkit import taskmanager
from temboardagent.routing import RouteSet
from temboardagent.toolkit.configuration import OptionSpec
from temboardagent.toolkit.validators import file_, commalist
from temboardagent.queue import Queue, Message
from temboardagent.tools import now
from temboardagent.inventory import SysInfo
from temboardagent import __version__ as __VERSION__
from temboardagent.errors import UserError

from .inventory import host_info, instance_info
from .probes import (
    load_probes,
    probe_bgwriter,
    probe_blocks,
    probe_cpu,
    probe_db_size,
    probe_filesystems_size,
    probe_loadavg,
    probe_locks,
    probe_memory,
    probe_process,
    probe_replication,
    probe_sessions,
    probe_tblspc_size,
    probe_wal_files,
    probe_xacts,
    run_probes,
)
from .output import send_output, remove_passwords

logger = logging.getLogger(__name__)
workers = taskmanager.WorkerSet()
routes = RouteSet(prefix=b'/monitoring/probe')


@routes.get(b'/sessions')
def get_probe_sessions(http_context, app):
    return api_run_probe(probe_sessions(app.config.monitoring), app.config)


@routes.get(b'/xacts')
def get_probe_xacts(http_context, app):
    return api_run_probe(probe_xacts(app.config.monitoring), app.config)


@routes.get(b'/locks')
def get_probe_locks(http_context, app):
    return api_run_probe(probe_locks(app.config.monitoring), app.config)


@routes.get(b'/blocks')
def get_probe_blocks(http_context, app):
    return api_run_probe(probe_blocks(app.config.monitoring), app.config)


@routes.get(b'/bgwriter')
def get_probe_bgwriter(http_context, app):
    return api_run_probe(probe_bgwriter(app.config.monitoring), app.config)


@routes.get(b'/db_size')
def get_probe_db_size(http_context, app):
    return api_run_probe(probe_db_size(app.config.monitoring), app.config)


@routes.get(b'/tblspc_size')
def get_probe_tblspc_size(http_context, app):
    return api_run_probe(probe_tblspc_size(app.config.monitoring), app.config)


@routes.get(b'/filesystems_size')
def get_probe_filesystems_size(http_context, app):
    return api_run_probe(probe_filesystems_size(app.config.monitoring),
                         app.config)


@routes.get(b'/cpu')
def get_probe_cpu(http_context, app):
    return api_run_probe(probe_cpu(app.config.monitoring), app.config)


@routes.get(b'/process')
def get_probe_process(http_context, app):
    return api_run_probe(probe_process(app.config.monitoring), app.config)


@routes.get(b'/memory')
def get_probe_memory(http_context, app):
    return api_run_probe(probe_memory(app.config.monitoring), app.config)


@routes.get(b'/loadavg')
def get_probe_loadavg(http_context, app):
    return api_run_probe(probe_loadavg(app.config.monitoring), app.config)


@routes.get(b'/wal_files')
def get_probe_wal_files(http_context, app):
    return api_run_probe(probe_wal_files(app.config.monitoring), app.config)


@routes.get(b'/replication')
def get_probe_replication(http_context, app):
    return api_run_probe(probe_replication(app.config.monitoring), app.config)


def api_run_probe(probe_instance, config):
    """
    Run a probe instance.
    """
    conninfo = dict(
        host=config.postgresql.host,
        port=config.postgresql.port,
        user=config.postgresql.user,
        database=config.postgresql.dbname,
        password=config.postgresql.password,
        dbnames=config.monitoring.dbnames,
        instance=config.postgresql.instance,
    )
    # Validate connection information from the config, and ensure
    # the instance is available
    sysinfo = SysInfo()
    hostname = sysinfo.hostname(config.temboard.hostname)
    instance = instance_info(conninfo, hostname)
    # Set home path
    probe_instance.set_home(config.temboard.home)
    # Gather the data from probes
    return run_probes([probe_instance], [instance], delta=False)


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
    probes = load_probes(config.monitoring, config.temboard.home)

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
    q = Queue(os.path.join(config.temboard.home, 'metrics.q'),
              max_size=1024 * 1024 * 10, overflow_mode='slide')
    q.push(Message(content=json.dumps(output)))
    logger.debug("Done")


@workers.register(pool_size=1)
def monitoring_sender_worker(app):
    config = app.config
    c = 0
    logger.debug("Starting sender")
    q = Queue(os.path.join(config.temboard.home, 'metrics.q'),
              max_size=1024 * 1024 * 10, overflow_mode='slide')
    while True:
        # Let's do it smoothly..
        time.sleep(0.5)
        msg = q.shift(delete=False)

        if msg is None:
            # If we get nothing from the queue then we get out from this while
            # loop.
            break
        try:
            # Try to send data to temboard collector API
            logger.debug("Trying to send data to collector")
            logger.debug(config.monitoring.collector_url)
            logger.debug(msg.content)
            send_output(
                config.monitoring.ssl_ca_cert_file,
                config.monitoring.collector_url,
                config.temboard.key,
                msg.content
            )
        except HTTPError as e:
            # On error 409 (DB Integrity) we just drop the message and move to
            # the next message.
            if int(e.code) == 409:
                continue

            try:
                data = e.read()
                data = json.loads(data)
                message = data['error']
            except Exception as e:
                logger.debug("Can't get error details: %s", e)
                message = str(e)

            logger.error("Failed to send data to collector: %s", message)
            logger.error("You should find details in temBoard UI logs.")

            raise Exception("Failed to send data to collector.")

        # If everything's fine then remove current msg from the queue
        # Integrity check is made using check_msg
        q.shift(delete=True, check_msg=msg)

        if c > 60:
            break
        c += 1

    logger.debug("Done")


class MonitoringPlugin(object):
    PG_MIN_VERSION = 90400
    s = 'monitoring'
    option_specs = [
        OptionSpec(s, 'dbnames', default='*', validator=commalist),
        OptionSpec(s, 'scheduler_interval', default=60, validator=int),
        OptionSpec(s, 'probes', default='*', validator=commalist),
        OptionSpec(s, 'collector_url', default=OptionSpec.REQUIRED),
        OptionSpec(s, 'ssl_ca_cert_file', default=None, validator=file_),
    ]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def load(self):
        pg_version = self.app.postgres.fetch_version()
        if pg_version < self.PG_MIN_VERSION:
            msg = "%s is incompatible with Postgres below 9.4" % (
                self.__class__.__name__)
            raise UserError(msg)

        self.app.router.add(routes)
        self.app.worker_pool.add(workers)
        workers.schedule(
            id='monitoring_collector',
            redo_interval=self.app.config.monitoring.scheduler_interval,
        )(monitoring_collector_worker)
        workers.schedule(
            id='monitoring_sender',
            redo_interval=self.app.config.monitoring.scheduler_interval,
        )(monitoring_sender_worker)
        self.app.scheduler.add(workers)

    def unload(self):
        self.app.scheduler.remove(workers)
        self.app.worker_pool.remove(workers)
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.option_specs)
