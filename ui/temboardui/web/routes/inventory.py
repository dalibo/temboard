import codecs
import logging
from io import StringIO

import flask
import sqlalchemy
from flask import current_app, g

from ... import agentclient
from ...model import QUERIES, orm
from ...toolkit.utils import utcnow
from ..flask import admin_required, transaction

logger = logging.getLogger(__name__)


@current_app.route("/settings/groups/instance")
@admin_required
def get_instance_groups_html():
    return flask.render_template(
        "settings/instance-groups.html",
        nav=True,
        role=g.current_user,
        vitejs=current_app.vitejs,
        groups=orm.Groups.all("instance").with_session(g.db_session).all(),
    )


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

    try:
        instance = (
            orm.Instances.insert(
                agent_address=j["agent_address"],
                agent_port=j["agent_port"],
                discover=j["discover"],
                discover_etag=j["discover_etag"],
                # put_instance will handle other attributes.
            )
            .with_session(g.db_session)
            .one()
        )
    except sqlalchemy.exc.IntegrityError as e:
        logger.warning("Failed to insert instance: %s", e)
        flask.abort(400, "Instance already registered.")

    g.db_session.flush()
    return put_instance(instance=instance)


@current_app.route("/json/instances/<address>/<port>")
@admin_required
def get_instance(address, port):
    try:
        instance = orm.Instances.get(address, port).with_session(g.db_session).one()
    except sqlalchemy.orm.exc.NoResultFound:
        flask.abort(404, "Instance not found.")
    return flask.jsonify(instance.asdict())


@current_app.route("/json/instances/<address>/<port>", methods=["PUT"])
@admin_required
@transaction
def put_instance(address=None, port=None, instance=None):
    if not instance:
        try:
            instance = orm.Instances.get(address, port).with_session(g.db_session).one()
        except sqlalchemy.orm.exc.NoResultFound:
            flask.abort(404, "Instance not found.")

    j = flask.request.json

    try:
        instance.discover = j["discover"]
        instance.discover_etag = j["discover_etag"]
        instance.discover_date = utcnow()
        instance.hostname = j["discover"]["system"]["fqdn"]
        instance.pg_port = j["discover"]["postgresql"]["port"]
    except KeyError:
        logger.debug("Missing discover. Keeping old informations.")
    instance.notify = j["notify"]
    instance.comment = j["comment"] or ""
    g.db_session.add(instance)
    g.db_session.flush()

    current_groups = {g.group_name for g in instance.groups}
    new_groups = set(j["groups"])
    for i, group in reversed(list(enumerate(instance.groups))):
        if group.group_name not in new_groups:
            del instance.groups[i]
    for group in new_groups - current_groups:
        try:
            group = (
                orm.Groups.get(kind="instance", name=group)
                .with_session(g.db_session)
                .one()
            )
        except sqlalchemy.orm.exc.NoResultFound:
            flask.abort(400, f"Unknown group {group}.")

        g.db_session.execute(instance.add_group(group))
    g.db_session.flush()

    current_plugins = {p.plugin_name for p in instance.plugins}
    new_plugins = set(j["plugins"])
    for i, plugin in reversed(list(enumerate(instance.plugins))):
        if plugin.plugin_name not in new_plugins:
            del instance.plugins[i]
    for plugin in new_plugins - current_plugins:
        if plugin not in current_app.temboard.plugins:
            flask.abort(400, f"Unknown plugin {plugin}.")
        g.db_session.execute(instance.enable_plugin(plugin))

    g.db_session.flush()
    return flask.jsonify(instance.asdict())


@current_app.route("/json/instances/<address>/<port>", methods=["DELETE"])
@admin_required
@transaction
def delete_instance(address, port):
    out = g.db_session.execute(orm.Instances.delete(address, port))
    if out.rowcount == 0:
        flask.abort(404, "Instance not found.")
    return flask.jsonify()


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


@current_app.route("/instances.csv")
@admin_required
def get_instances_csv():
    search = flask.request.args.get("filter")
    pattern = "%%%s%%" % search if search else "%"
    bind = g.db_session.get_bind()
    conn = bind.raw_connection().connection
    sql = QUERIES["copy-instances-as-csv"]
    with conn.cursor() as cur, StringIO() as fo:
        sql = cur.mogrify(sql, (pattern,))
        cur.copy_expert(sql, fo)
        csv = fo.getvalue()

    filename = "postgresql-instances-inventory.csv"
    return flask.make_response(
        # BOM declares UTF8 for Excel.
        codecs.BOM_UTF8 + csv.encode("utf-8"),
        200,
        {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment;filename=" + filename,
        },
    )
