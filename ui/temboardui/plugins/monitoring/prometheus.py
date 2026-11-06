import logging

from flask import current_app

from .chartdata import METRICS

logger = logging.getLogger(__name__)


class Disabled(Exception):
    """
    Prometheus is disabled on this installation or for this metric.
    """

    pass


def query_data(metric, key, server, start, end):
    if not current_app.temboard.config.monitoring.prometheus_url:
        raise Disabled()
    promql = METRICS[metric].get("promql")
    if not promql:
        raise Disabled()
    promql = promql % {"server": server, "key": key}
    raise Disabled()
