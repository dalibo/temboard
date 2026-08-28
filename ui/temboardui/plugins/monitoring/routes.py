# Flask routes
from flask import current_app

from ...web.flask import instance_proxy


@instance_proxy.route("/monitoring/metrics")
def get_metrics():
    return current_app.instance.proxy()
