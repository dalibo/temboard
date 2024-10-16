import codecs
import logging
from io import StringIO

import flask
import sqlalchemy
from flask import current_app, g

from ... import agentclient
from ...model import QUERIES, orm
from ...toolkit import validators
from ...toolkit.utils import utcnow
from ..flask import admin_required, transaction, validating

logger = logging.getLogger(__name__)


@current_app.route("/json/environments")
@admin_required
def get_environments():
    return flask.jsonify(
        [e.asdict() for e in orm.Environment.all().with_session(g.db_session)]
    )


@current_app.route("/json/environments", methods=["POST"])
@admin_required
@transaction
def post_environments():
    return put_environment(environment=orm.Environment(dba_group=orm.Group()))


@current_app.route("/json/environments/<name>")
@admin_required
def get_environment(name):
    environment = orm.Environment.get(name).with_session(g.db_session).first()
    if environment is None:
        flask.abort(404, "No such environment.")
    return flask.jsonify(environment.asdict())


@current_app.route("/json/environments/<name>/members")
@admin_required
def get_environment_members(name):
    return flask.jsonify(
        [
            {k: getattr(r, k) for k in r.keys()}
            for r in g.db_session.execute(orm.Environment.select_memberships(name))
        ]
    )


@current_app.route("/json/environments/<name>", methods=["PUT"])
@admin_required
@transaction
def put_environment(name=None, environment=None):
    if environment is None:
        environment = orm.Environment.get(name).with_session(g.db_session).first()
    if environment is None:
        flask.abort(404, "No such environment.")

    with validating():
        environment.name = validators.slug(flask.request.json["name"])
    environment.description = flask.request.json["description"]
    environment.dba_group.name = f"{environment.name}/dba"
    # Used as profile name in /settings/environment/<>/members
    environment.dba_group.description = "DBA"
    g.db_session.add(environment)  # When called from post_environment
    g.db_session.flush()

    return flask.jsonify(environment.asdict())


@current_app.route("/json/environments/<name>", methods=["DELETE"])
@admin_required
@transaction
def delete_environment(name):
    # Delete DBA group, cascding to environment.
    result = g.db_session.execute(orm.Group.delete(f"{name}/dba"))
    if result.rowcount == 0:
        flask.abort(404, "No such environment.")
    return flask.jsonify()


@current_app.route("/json/instances", methods=["POST"])
@transaction
def post_instance():
    j = flask.request.json
    environment = (
        orm.Environment.get(j["environment"]).with_session(g.db_session).first()
    )
    if environment is None:
        flask.abort(400, "Unknown environment")
    try:
        instance = (
            orm.Instance.insert(
                agent_address=j["agent_address"],
                agent_port=j["agent_port"],
                discover=j["discover"],
                discover_etag=j["discover_etag"],
                environment=j["environment"],
                # put_instance will handle other attributes.
            )
            .with_session(g.db_session)
            .one()
        )
    except sqlalchemy.exc.IntegrityError as e:
        logger.warning("Failed to insert instance: %s", e)
        flask.abort(400, "Instance already registered.")

    # insert does not populate environment nor plugins.
    instance.environment = environment

    g.db_session.flush()
    return put_instance(instance=instance)


@current_app.route("/json/instances/<address>/<port>")
@admin_required
def get_instance(address, port):
    try:
        instance = orm.Instance.get(address, port).with_session(g.db_session).one()
    except sqlalchemy.orm.exc.NoResultFound:
        flask.abort(404, "Instance not found.")
    return flask.jsonify(instance.asdict())


@current_app.route("/json/instances/<address>/<port>", methods=["PUT"])
@admin_required
@transaction
def put_instance(address=None, port=None, instance=None):
    if not instance:
        try:
            instance = orm.Instance.get(address, port).with_session(g.db_session).one()
        except sqlalchemy.orm.exc.NoResultFound:
            flask.abort(404, "Instance not found.")

    j = flask.request.json

    try:
        instance.discover = j["discover"]
        instance.discover_etag = j["discover_etag"]
        instance.discover_date = utcnow()
        instance.hostname = j["discover"]["system"]["fqdn"]
        instance.pg_port = j["discover"]["postgres"]["port"]
    except KeyError:
        logger.debug("Missing discover. Keeping old informations.")
    instance.notify = j["notify"]
    instance.comment = j["comment"] or ""
    if j["environment"] != instance.environment.name:
        instance.environment = (
            orm.Environment.get(j["environment"]).with_session(g.db_session).first()
        )
    if instance.environment is None:
        flask.abort(400, "Unknown environment.")
    g.db_session.add(instance)
    g.db_session.flush()

    current_plugins = {p.plugin_name for p in instance.plugins}
    new_plugins = set(j["plugins"])
    for plugin in current_plugins:
        if plugin not in new_plugins:
            g.db_session.execute(instance.disable_plugin(plugin))
    for plugin in new_plugins - current_plugins:
        if plugin not in current_app.temboard.plugins:
            logger.debug("Plugin not enabled on UI: %s", plugin)
            continue
        g.db_session.execute(instance.enable_plugin(plugin))

    return flask.jsonify(instance.asdict())


@current_app.route("/json/instances/<address>/<port>", methods=["DELETE"])
@admin_required
@transaction
def delete_instance(address, port):
    out = g.db_session.execute(orm.Instance.delete(address, port))
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
    sql = QUERIES["instances-copy-as-csv"]
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
