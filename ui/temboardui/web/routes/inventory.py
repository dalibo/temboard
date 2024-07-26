import logging

import flask
from flask import current_app, g

from ... import agentclient
from ...model import orm
from ..flask import admin_required

logger = logging.getLogger(__name__)


@current_app.route("/json/groups/instance")
@admin_required
def get_instance_groups():
    """List instance groups."""
    return flask.jsonify(
        [g.asdict() for g in orm.Groups.all("instance").with_session(g.db_session)]
    )


# Special proxy for unregistered instance.
@current_app.route("/json/instances/<address>/<port>/discover")
@admin_required
def discover(address, port):
    client = agentclient.TemboardAgentClient.factory(
        current_app.temboard.config, address, port, username=g.current_user.role_name
    )
    try:
        response = client.get("/discover")
        response.raise_for_status()
    except OSError as e:
        logger.warning("Failed to discover agent at %s:%s: %s", address, port, e)
        flask.abort(
            400,
            "Can't connect to agent. "
            "Please check address and port or that agent is running.",
        )
    return flask.jsonify(response.json())
