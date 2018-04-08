import logging
import json
import os
from pickle import dumps as pickle, loads as unpickle

from temboardagent.scheduler import taskmanager
from temboardagent.spc import connector
from temboardagent.configuration import OptionSpec
from temboardagent.routing import add_route
from temboardagent.queue import Queue, Message
from temboardagent.errors import UserError

<<<<<<< HEAD
if not __name__.startswith('temboardagent.plugins.'):
    raise ImportError("Migrated to new plugin API.")

import metrics
=======
from . import metrics
>>>>>>> aa40809... fixup! Migrate dashboard plugin

logger = logging.getLogger(__name__)
CONFIG = None


def dashboard(http_context, app):
    return metrics.get_metrics_queue(app.config)


def dashboard_config(http_context, app):
    return dict(
        scheduler_interval=app.config.dashboard.scheduler_interval,
        history_length=app.config.dashboard.history_length,
    )


def dashboard_live(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_metrics(conn, app.config)


def dashboard_history(http_context, app):
    return metrics.get_history_metrics_queue(app.config)


def dashboard_buffers(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_buffers(conn)


def dashboard_hitratio(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_hitratio(conn)


def dashboard_active_backends(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_active_backends(conn)


def dashboard_cpu(http_context, app):
    return metrics.get_cpu_usage()


def dashboard_loadaverage(http_context, app):
    return metrics.get_loadaverage()


def dashboard_memory(http_context, app):
    return metrics.get_memory_usage()


def dashboard_hostname(http_context, app):
    return metrics.get_hostname(app.config)


def dashboard_os_version(http_context, app):
    return metrics.get_os_version()


def dashboard_pg_version(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_pg_version(conn)


def dashboard_n_cpu(http_context, app):
    return metrics.get_n_cpu()


def dashboard_databases(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_databases(conn)


def dashboard_info(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_info(conn, app.config)


def dashboard_max_connections(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_max_connections(conn)


def dashboard_collector_worker(pickled_config):
    logger.debug("Starting to collect dashboard data")
    config = unpickle(pickled_config)
    conn = connector(
        host=config.postgresql.host,
        port=config.postgresql.port,
        user=config.postgresql.user,
        password=config.postgresql.password,
        database=config.postgresql.dbname,
    )
    conn.connect()
    # Collect data
    data = metrics.get_metrics(conn, config)
    conn.close()

    # We don't want to store notifications in the history.
    data.pop('notifications', None)
    q = Queue(os.path.join(config.temboard.home, 'dashboard.q'),
              max_length=(config.dashboard.history_length + 1),
              overflow_mode='slide')

    q.push(Message(content=json.dumps(data)))
    logger.debug(data)
    logger.debug("End")


def dashboard_collector_bootstrap(context):
    yield taskmanager.Task(
        worker_name='dashboard_collector_worker',
        id='dashboard_collector',
        options={'pickled_config': pickle(CONFIG)},
        redo_interval=CONFIG.dashboard.scheduler_interval,
    )


class DashboardPlugin(object):
    PG_MIN_VERSION = 90400

    def __init__(self, app, **kw):
        self.app = app
        s = 'dashboard'
        self.app.config.add_specs([
            OptionSpec(s, 'scheduler_interval', default=2, validator=int),
            OptionSpec(s, 'history_length', default=150, validator=int),
        ])

    def load(self):
        global CONFIG
        CONFIG = self.app.config

        pg_version = self.app.postgres.fetch_version()
        if pg_version < self.PG_MIN_VERSION:
            msg = "%s is incompatible with Postgres below %s" % (
                self.__class__.__name__, self.PG_MIN_VERSION)
            raise UserError(msg)

        add_route('GET', '/dashboard')(dashboard)
        add_route('GET', '/dashboard/config')(dashboard_config)
        add_route('GET', '/dashboard/live')(dashboard_live)
        add_route('GET', '/dashboard/history')(dashboard_history)
        add_route('GET', '/dashboard/buffers')(dashboard_buffers)
        add_route('GET', '/dashboard/hitratio')(dashboard_hitratio)
        add_route('GET', '/dashboard/active_backends')(
            dashboard_active_backends)
        add_route('GET', '/dashboard/cpu')(dashboard_cpu)
        add_route('GET', '/dashboard/loadaverage')(dashboard_loadaverage)
        add_route('GET', '/dashboard/memory')(dashboard_memory)
        add_route('GET', '/dashboard/hostname')(dashboard_hostname)
        add_route('GET', '/dashboard/os_version')(dashboard_os_version)
        add_route('GET', '/dashboard/pg_version')(dashboard_pg_version)
        add_route('GET', '/dashboard/n_cpu')(dashboard_n_cpu)
        add_route('GET', '/dashboard/databases')(dashboard_databases)
        add_route('GET', '/dashboard/info')(dashboard_info)
        add_route('GET', '/dashboard/max_connections')(
            dashboard_max_connections)
        taskmanager.worker(pool_size=1)(dashboard_collector_worker)
        taskmanager.bootstrap()(dashboard_collector_bootstrap)

    def unload(self):
        pass
