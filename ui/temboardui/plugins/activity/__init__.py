from flask import current_app, jsonify
from flask import render_template as flask_render_template

from ...web.flask import instance_proxy, instance_routes


class ActivityPlugin:
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        instance_proxy.generic_proxy("/activity/kill", method="POST")


@instance_routes.route("/activity")
def activity():
    current_app.instance.check_active_plugin("activity")
    current_app.instance.fetch_status()
    return flask_render_template("activity.html", plugin="activity")


@instance_proxy.route("/activity")
def activity_proxy():
    # DEPRECATED: move to new agent endpoints for activity.
    return jsonify(
        dict(
            blocking=current_app.instance.request("/activity/blocking").json(),
            running=current_app.instance.request("/activity").json(),
            waiting=current_app.instance.request("/activity/waiting").json(),
        )
    )
