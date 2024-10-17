import logging

from . import discover
from .postgres import extract_conninfo_fields
from .queries import QUERIES

logger = logging.getLogger(__name__)


class Status:
    def __init__(self, app):
        self.app = app
        self.data = dict(postgres=dict(available=True), temboard=dict(), system=dict())

    def get(self, conn=None):
        self.data["postgres"] = {}
        self.data["system"] = {}
        self.data["temboard"] = {}
        discover_data = self.app.discover.ensure_latest()
        with self.app.postgres.maybe_connect(conn=conn) as conn:
            logger.debug("Inspecting Postgres instance.")
            collect_postgres(self.data, conn, discover_data)
        self.data["temboard"]["status"] = "running"
        self.data["temboard"]["pid"] = self.app.pid
        self.data["temboard"]["start_time"] = self.app.start_datetime
        self.data["system"]["status"] = "running"
        self.data["system"]["start_time"] = discover_data["system"]["start_time"]
        # Collect CPU and memory info in case of hotplug.
        discover.collect_cpu(self.data)
        discover.collect_memory(self.data)
        return self.data


def collect_postgres(data, conn, discover_data):
    data["postgres"]["status"] = "running"
    data["postgres"]["pid"] = discover_data["postgres"]["pid"]
    data["postgres"]["start_time"] = discover_data["postgres"]["start_time"]
    try:
        row = conn.queryone(QUERIES["status"])
        data["postgres"].update(row)
        conninfo = extract_conninfo_fields(data["postgres"]["primary_conninfo"])
        data["postgres"]["primary"] = conninfo
        data["postgres"]["primary_conninfo"] = " ".join(
            f"{k}={v}" for k, v in conninfo.items()
        )
    except Exception as e:
        logger.warning("Cannot collect extra Postgres info: %s", e)
