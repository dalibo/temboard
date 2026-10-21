# Flask routes
from flask import current_app, g, jsonify, request

from ....model import orm
from ....web.flask import apikey_allowed, instance_proxy


@instance_proxy.route("/monitoring/metrics")
@apikey_allowed
def get_metrics():
    return current_app.instance.proxy()


@current_app.route("/json/prometheus/targets")
@apikey_allowed
def get_prometheus_targets():
    # Prometheus HTTP service discovery. Each agent metrics endpoint is
    # scraped through temBoard UI proxy, hence the target is temBoard UI
    # itself, as reached by Prometheus.
    targets = []
    for instance in orm.Instance.all().with_session(g.db_session):
        if not instance.discover:
            continue
        if "monitoring" not in instance.discover["temboard"]["plugins"]:
            continue
        address, port = instance.agent_address, instance.agent_port
        targets.append(
            dict(
                targets=[request.host],
                labels=dict(
                    __metrics_path__=f"/proxy/{address}/{port}/monitoring/metrics",
                    nodename=instance.hostname,
                    server=f"{instance.hostname}:{instance.pg_port}",
                    instance=f"{instance.hostname}:{instance.pg_port}",
                    environment=instance.environment.name,
                    temboard_agent=f"{address}:{port}",
                ),
            )
        )
    return jsonify(targets)
