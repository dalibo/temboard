# Flask routes
from flask import current_app

from ...web.flask import apikey_allowed, instance_proxy


@instance_proxy.route('/monitoring/metrics')
@apikey_allowed
def get_metrics():
    return current_app.instance.proxy()
