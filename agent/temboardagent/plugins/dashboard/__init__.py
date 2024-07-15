import logging
import time

from bottle import default_app

from ...toolkit import logfmt, taskmanager
from ...toolkit.configuration import OptionSpec
from ...toolkit.utils import utcnow
from ...web.app import CustomBottle
from . import db, metrics

bottle = CustomBottle()
logger = logging.getLogger(__name__)
workers = taskmanager.WorkerSet()


@bottle.get("/")
def dashboard(pgconn):
    out = metrics.get_metrics_queue(default_app().temboard.config)
    out["status"] = default_app().temboard.status.get(conn=pgconn)
    return out


@bottle.get("/config")
def dashboard_config():
    app = default_app().temboard
    return dict(
        scheduler_interval=app.config.dashboard.scheduler_interval,
        history_length=app.config.dashboard.history_length,
    )


@bottle.get("/history")
def dashboard_history():
    return metrics.get_history_metrics_queue(default_app().temboard.config)


@workers.register(pool_size=1)
def dashboard_collector_worker(app, pool=None):
    logger.info("Collecting metrics.")

    data = metrics.get_metrics(app, pool)

    # We don't want to store notifications in the history.
    data.pop("notifications", None)
    logger.debug(logfmt.format(**data))

    db.add_metric(
        app.config.temboard.home,
        "dashboard.db",
        time.time(),
        data,
        app.config.dashboard.history_length,
    )


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
                for attempt in pool.auto_reconnect():
                    with attempt:
                        dashboard_collector_worker(app, pool)
            except Exception as e:
                logger.error("Dashboard collector error: %s", e)

        elapsed = utcnow() - start
        elapsed = elapsed.total_seconds()


class DashboardPlugin:
    PG_MIN_VERSION = (90400, 9.4)
    s = "dashboard"
    option_specs = [
        OptionSpec(s, "scheduler_interval", default=2, validator=int),
        OptionSpec(s, "history_length", default=150, validator=int),
    ]
    del s

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.option_specs)

    def bootstrap(self):
        db.bootstrap(self.app.config.temboard.home, "dashboard.db")

    def load(self):
        default_app().mount("/dashboard", bottle)
        self.app.worker_pool.add(workers)
        workers.schedule(id="dashboard_collector_batch", redo_interval=BATCH_DURATION)(
            dashboard_collector_batch_worker
        )
        self.app.scheduler.add(workers)
