#
# Somes notes on monitoring in temBoard
#
# Metrics are stored in different tables:
#
# - metric_*_current stores metrics one row per metric point
# - metric_*_30m_current is a compacted COPY of _current by interval
# - metric_*_history aggregates points per time interavl
#
# Tasks:
#
# - schedule_collector(): schedule a collector task for each agent in
#   inventory.
# - collector(host, port, key) inserts metrics history in metric_*_current
#   table.
# - history_tables_worker() move data from metric_*_current to
#   metric_*_history, grouped by time range. metric table is truncated
# - aggregate_data_worker() aggregates data in metric_*_30m_current and
#   metric_*_6h_current.
#

import shutil

from temboardtoolkit import validators as v
from temboardtoolkit.configuration import OptionSpec

from .tasks import workers


class MonitoringPlugin:
    s = "monitoring"
    prometheus = shutil.which("prometheus")
    options_specs = [
        OptionSpec(s, "collect_max_duration", default=30, validator=int),
        OptionSpec(s, "prometheus", default=prometheus, validator=v.file_),
    ]

    def __init__(self, app):
        self.app = app
        self.app.config.add_specs(self.options_specs)

    def load(self):
        # Import Flask routes
        __import__(__name__ + ".routes.prometheus")
        __import__(__name__ + ".routes.monitoring")
        __import__(__name__ + ".routes.alerting")
        self.app.worker_pool.add(workers)
        self.app.scheduler.add(workers)
