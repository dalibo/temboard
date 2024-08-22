import logging

from flask import current_app, render_template

from ...agentclient import TemboardAgentClient
from ...web.flask import instance_routes

logger = logging.getLogger(__name__)


@instance_routes.route("/dashboard")
def dashboard():
    current_app.instance.check_active_plugin("dashboard")

    try:
        config = current_app.instance.request("/dashboard/config").json()
    except TemboardAgentClient.Error as e:
        if 404 != e.code:
            raise
        logger.debug("Fallback dashboard config.")
        config = {"history_length": 150, "scheduler_interval": 2}

    history = current_app.instance.request("/dashboard/history").json()

    current_app.instance.fetch_status()
    dashboard = history[-1] if history else {}
    return render_template(
        "dashboard.html",
        plugin="dashboard",
        config=config,
        dashboard=dashboard,
        history=history or "",
    )
