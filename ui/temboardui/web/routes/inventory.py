import logging

import flask
import sqlalchemy
from flask import current_app, g

from ... import agentclient
from ...model import orm
from ..flask import admin_required, transaction

logger = logging.getLogger(__name__)


@current_app.route("/json/groups/instance")
@admin_required
def get_instance_groups():
    """List instance groups."""
    return flask.jsonify(
        [g.asdict() for g in orm.Groups.all("instance").with_session(g.db_session)]
    )


@current_app.route("/json/instances", methods=["POST"])
@transaction
def post_instance():
    j = flask.request.json

    groups = []
    for group in j["groups"]:
        try:
            group = (
                orm.Groups.get(kind="instance", name=group)
                .with_session(g.db_session)
                .one()
            )
        except sqlalchemy.orm.exc.NoResultFound:
            flask.abort(400, f"Unknown group {group}.")
        groups.append(group)

    plugins = []
    for p in j["plugins"]:
        if p not in current_app.temboard.plugins:
            flask.abort(400, f"Unknown plugin {p}.")
        plugins.append(p)

    try:
        instance = (
            orm.Instances.insert(
                agent_address=j["agent_address"],
                agent_port=j["agent_port"],
                discover=j["discover"],
                discover_etag=j["discover_etag"],
                notify=j["notify"],
                comment=j["comment"],
            )
            .with_session(g.db_session)
            .one()
        )
    except sqlalchemy.exc.IntegrityError as e:
        logger.warning("Failed to insert instance: %s", e)
        flask.abort(400, "Instance already registered.")

    for group in groups:
        g.db_session.execute(instance.add_group(group))

    for plugin in plugins:
        g.db_session.execute(instance.enable_plugin(plugin))

    return flask.jsonify(instance.asdict())


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
            401,
            "Can't connect to agent. "
            "Please check address and port or that agent is running.",
        )
    return flask.jsonify(response.json())
