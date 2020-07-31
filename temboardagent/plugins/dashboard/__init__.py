import logging
import time

from temboardagent.toolkit import taskmanager
from temboardagent.toolkit.configuration import OptionSpec
from temboardagent.routing import RouteSet

from . import db
from . import metrics

logger = logging.getLogger(__name__)
routes = RouteSet(prefix=b'/dashboard')
workers = taskmanager.WorkerSet()


@routes.get(b'', check_key=True)
def dashboard(http_context, app):
    return metrics.get_metrics_queue(app.config)


@routes.get(b'/config', check_key=True)
def dashboard_config(http_context, app):
    return dict(
        scheduler_interval=app.config.dashboard.scheduler_interval,
        history_length=app.config.dashboard.history_length,
    )


@routes.get(b'/live', check_key=True)
def dashboard_live(http_context, app):
    return metrics.get_metrics(app)


@routes.get(b'/history', check_key=True)
def dashboard_history(http_context, app):
    return metrics.get_history_metrics_queue(app.config)


@routes.get(b'/buffers', check_key=True)
def dashboard_buffers(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_buffers(conn)


@routes.get(b'/hitratio', check_key=True)
def dashboard_hitratio(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_hitratio(conn)


@routes.get(b'/active_backends', check_key=True)
def dashboard_active_backends(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_active_backends(conn)


@routes.get(b'/cpu', check_key=True)
def dashboard_cpu(http_context, app):
    return metrics.get_cpu_usage()


@routes.get(b'/loadaverage', check_key=True)
def dashboard_loadaverage(http_context, app):
    return metrics.get_loadaverage()


@routes.get(b'/memory', check_key=True)
def dashboard_memory(http_context, app):
    return metrics.get_memory_usage()


@routes.get(b'/hostname', check_key=True)
def dashboard_hostname(http_context, app):
    return metrics.get_hostname(app.config)


@routes.get(b'/os_version', check_key=True)
def dashboard_os_version(http_context, app):
    return metrics.get_os_version()


@routes.get(b'/pg_version', check_key=True)
def dashboard_pg_version(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_pg_version(conn)


@routes.get(b'/n_cpu', check_key=True)
def dashboard_n_cpu(http_context, app):
    return metrics.get_n_cpu()


@routes.get(b'/databases', check_key=True)
def dashboard_databases(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_databases(conn)


@routes.get(b'/info', check_key=True)
def dashboard_info(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_info(conn, app.config)


@routes.get(b'/max_connections', check_key=True)
def dashboard_max_connections(http_context, app):
    with app.postgres.connect() as conn:
        return metrics.get_max_connections(conn)


@workers.register(pool_size=1)
def dashboard_collector_worker(app):
    logger.debug("Starting dashboard collector")

    data = metrics.get_metrics(app)

    # We don't want to store notifications in the history.
    data.pop('notifications', None)
    logger.debug(data)

    db.add_metric(
        app.config.temboard.home,
        'dashboard.db',
        time.time(),
        data,
        app.config.dashboard.history_length
    )

    logger.debug("Done")


class DashboardPlugin(object):
    PG_MIN_VERSION = (90400, 9.4)
    s = 'dashboard'
    option_specs = [
        OptionSpec(s, 'scheduler_interval', default=2, validator=int),
        OptionSpec(s, 'history_length', default=150, validator=int),
    ]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def bootstrap(self):
        db.bootstrap(self.app.config.temboard.home, 'dashboard.db')

    def load(self):
        self.app.router.add(routes)
        self.app.worker_pool.add(workers)
        workers.schedule(
            id='dashboard_collector',
            redo_interval=self.app.config.dashboard.scheduler_interval
        )(dashboard_collector_worker)
        self.app.scheduler.add(workers)

    def unload(self):
        self.app.scheduler.remove(workers)
        self.app.worker_pool.remove(workers)
        self.app.router.remove(routes)
        self.app.config.remove_specs(self.option_specs)
