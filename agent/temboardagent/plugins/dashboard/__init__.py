import logging
import time

from bottle import Bottle, default_app

from ...toolkit import taskmanager
from ...toolkit.configuration import OptionSpec
from ...toolkit.utils import utcnow

from . import db
from . import metrics


bottle = Bottle()
logger = logging.getLogger(__name__)
workers = taskmanager.WorkerSet()


@bottle.get('/')
def dashboard():
    return metrics.get_metrics_queue(default_app().temboard.config)


@bottle.get('/config')
def dashboard_config():
    app = default_app().temboard
    return dict(
        scheduler_interval=app.config.dashboard.scheduler_interval,
        history_length=app.config.dashboard.history_length,
    )


@bottle.get('/live')
def dashboard_live(pgpool):
    return metrics.get_metrics(default_app().temboard, pgpool)


@bottle.get('/history')
def dashboard_history():
    return metrics.get_history_metrics_queue(default_app().temboard.config)


@bottle.get('/buffers')
def dashboard_buffers(pgconn):
    return metrics.get_buffers(pgconn)


@bottle.get('/hitratio')
def dashboard_hitratio(pgconn):
    return metrics.get_hitratio(pgconn)


@bottle.get('/active_backends')
def dashboard_active_backends(pgconn):
    return metrics.get_active_backends(pgconn)


@bottle.get('/cpu')
def dashboard_cpu():
    return metrics.get_cpu_usage()


@bottle.get('/loadaverage')
def dashboard_loadaverage():
    return metrics.get_loadaverage()


@bottle.get('/memory')
def dashboard_memory():
    return metrics.get_memory_usage()


@bottle.get('/hostname')
def dashboard_hostname():
    return metrics.get_hostname(default_app().temboard.config)


@bottle.get('/databases')
def dashboard_databases(pgconn):
    return metrics.get_databases(pgconn)


@workers.register(pool_size=1)
def dashboard_collector_worker(app, pool=None):
    logger.info("Running dashboard collector.")

    data = metrics.get_metrics(app, pool)

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


BATCH_DURATION = 5 * 60  # 5 minutes


@workers.register(pool_size=1)
def dashboard_collector_batch_worker(app):
    # Loop each configured interval in the batch duration.
    interval = app.config.dashboard.scheduler_interval
    pool = None
    start = utcnow()
    elapsed = 0
    while elapsed < BATCH_DURATION:
        if elapsed > 0:
            # Throttle interval after first run.
            time.sleep(interval)

        try:
            pool = pool or app.postgres.pool()
        except Exception as e:
            logger.error("Failed to connect to Postgres: %s", e)
        else:
            try:
                for attempt in pool.retry_connection():
                    with attempt:
                        dashboard_collector_worker(app, pool)
            except Exception as e:
                logger.error("Dashboard collector error: %s", e)

        elapsed = utcnow() - start
        elapsed = elapsed.total_seconds()


class DashboardPlugin:
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
        default_app().mount('/dashboard', bottle)
        self.app.worker_pool.add(workers)
        workers.schedule(
            id='dashboard_collector_batch',
            redo_interval=BATCH_DURATION,
        )(dashboard_collector_batch_worker)
        self.app.scheduler.add(workers)

    def unload(self):
        self.app.scheduler.remove(workers)
        self.app.worker_pool.remove(workers)
        self.app.config.remove_specs(self.option_specs)
