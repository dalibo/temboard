import datetime
import logging
from urllib.parse import urlparse

from flask import current_app
from temboardtoolkit.http import TemboardClient as HTTPClient

from .chartdata import METRICS

logger = logging.getLogger(__name__)


class Disabled(Exception):
    """
    Prometheus is disabled on this installation or for this metric.
    """

    pass


def make_prometheus_client():
    if not current_app.temboard.config.monitoring.prometheus_url:
        raise Disabled()
    url = urlparse(current_app.temboard.config.monitoring.prometheus_url)
    return HTTPClient(url.hostname, url.port, scheme=url.scheme)


def query_data(metric, key, server, start, end):
    prom = METRICS[metric].get("prometheus")
    if not prom:
        raise Disabled()
    query = prom["query"] % {"server": server, "key": key}

    client = make_prometheus_client()
    res = client.get(
        "/api/v1/query_range",
        query={
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": guess_step(end, start),
        },
    )
    res.raise_for_status()

    data = res.json()
    if data["status"] != "success":
        logger.warning("Prometheus failed. status=%s", data["status"])
        return []

    results = data["data"]["result"]
    # results is a set of series, one per metrics.
    # Sort series in wanted order.
    conforder = [m[0] for m in prom["map"]]
    results.sort(key=lambda r: conforder.index(r["metric"]["__name__"]))
    resorder = [r["metric"]["__name__"] for r in results]
    if conforder != resorder:
        raise Exception("Inconsistent query and map")

    serie = []
    serie.append(["date"] + [m[1] for m in prom["map"]])  # headers

    # zip series as [(t, v), (t, v), (t, v)]
    for points in zip(*[r["values"] for r in results]):
        t = datetime.datetime.fromtimestamp(float(points[0][0]), datetime.timezone.utc)
        # then convert as [t, v, v, v]
        row = [t]
        for point in points:
            value = point[1]
            if value:
                value = float(value)
            row.append(value)
        serie.append(row)

    return serie


def guess_step(end: datetime.datetime, start: datetime.datetime) -> int:
    delta = end - start
    minutes = delta.total_seconds() / 60  # How many minutes asked.
    minutes_per_point = max(1, minutes // 500)
    return int(60 * minutes_per_point)
