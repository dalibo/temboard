import logging
from time import sleep

import flask
from flask import current_app as app
from flask import g, jsonify, make_response, redirect, render_template, request
from tornado.web import create_signed_value

from temboardui.application import gen_cookie, get_role_by_auth, hash_password
from temboardui.errors import TemboardUIError

from ...model import orm
from ...toolkit import validators
from ..flask import admin_required, anonymous_allowed, transaction, validating

logger = logging.getLogger(__name__)


@app.route("/logout")
def logout():
    response = make_response(redirect("/"))
    response.delete_cookie("temboard")
    return response


@app.route("/login")
@anonymous_allowed
def login():
    if g.current_user:
        return redirect("/home")
    return render_template("login.html", headerbar=False)


@app.route(r"/json/login", methods=["POST"])
@anonymous_allowed
def json_login():
    username = request.json["username"]
    password = request.json["password"]

    response = make_response(jsonify({"message": "OK"}))
    passhash = hash_password(username, password).decode("utf-8")

    try:
        role = get_role_by_auth(g.db_session, username, passhash)
    except TemboardUIError as e:
        logger.error("Login failed: %s", e)
        response = make_response(jsonify({"error": "Wrong username/password."}))
        response.status_code = 401
        # Mitigate dictionnaries attacks.
        sleep(1)
        return response

    logger.info("Role '%s' authentificated.", role.role_name)
    secret_cookie = create_signed_value(
        app.temboard.config.temboard.cookie_secret,
        "temboard",
        gen_cookie(role.role_name, passhash),
    )
    response.set_cookie("temboard", secret_cookie.decode(), secure=True)
    return response


@app.route("/json/groups/role")
@admin_required
def get_groups():
    return flask.jsonify(
        [g.asdict() for g in orm.Groups.all("role").with_session(g.db_session)]
    )


@app.route("/json/groups/role", methods=["POST"])
@admin_required
@transaction
def post_group():
    with validating():
        validators.slug(request.json["name"])

    group = (
        orm.Groups.insert("role", request.json["name"], request.json["description"])
        .with_session(g.db_session)
        .one()
    )
    return flask.jsonify(group.asdict())


@app.route("/json/groups/role/<name>")
@admin_required
def get_group(name):
    group = orm.Groups.get("role", name).with_session(g.db_session).one_or_none()
    if group is None:
        flask.abort(404, "No such group.")
    return flask.jsonify(group.asdict())


@app.route("/json/groups/role/<name>", methods=["PUT"])
@admin_required
@transaction
def put_group(name, group=None):
    if group is None:
        group = orm.Groups.get("role", name).with_session(g.db_session).one_or_none()
    if group is None:
        flask.abort(404, "No such group.")

    with validating():
        validators.slug(request.json["name"])

    group.group_name = request.json["name"]
    group.group_description = request.json["description"]
    return flask.jsonify(group.asdict())


@app.route("/json/groups/role/<name>", methods=["DELETE"])
@admin_required
@transaction
def delete_group(name):
    """Delete a group of roles."""
    result = g.db_session.execute(orm.Groups.delete("role", name))
    if result.rowcount == 0:
        flask.abort(404, "No such group.")
    return flask.jsonify()


@app.route("/json/users", methods=["POST"])
@admin_required
@transaction
def post_user():
    if "password" not in request.json:
        raise flask.abort(400, "Password required.")
    role = orm.Role(groups=[])
    g.db_session.add(role)
    return put_user(user=role)


@app.route("/json/users/<name>")
@admin_required
def get_user(name):
    user = orm.Role.get(name).with_session(g.db_session).one_or_none()
    if user is None:
        flask.abort(404, "No such user.")
    return flask.jsonify(user.asdict())


@app.route("/json/users/<name>", methods=["PUT"])
@admin_required
@transaction
def put_user(name=None, user=None):
    j = request.json
    if user is None:
        user = orm.Role.get(name).with_session(g.db_session).one_or_none()
    if user is None:
        flask.abort(404, "No such user.")

    current_groups = {rxg.group_name for rxg in user.groups}
    wanted_groups = set(j["groups"])
    # Drop RoleGroups before renaming role because role name is in primary key and SA does not handle this.
    if user.groups:
        # Actually, we do not handle Groups but secondary table RoleGroups.
        for rxg in user.groups:
            if rxg.group_name in wanted_groups:
                continue
            g.db_session.delete(rxg)

        g.db_session.flush()

    user.is_admin = j["is_admin"]
    user.is_active = j["is_active"]
    if j["name"] in {"temboard"}:
        raise flask.abort(400, "Reserved user name.")

    with validating():
        user.role_name = validators.slug(j["name"])
        if j["email"]:
            user.role_email = validators.email(j["email"])
        elif user.role_email:
            user.role_email = None  # Remove email
        if j["phone"]:
            user.role_phone = validators.phone(j["phone"])
        if j.get("password"):
            validators.password(j["password"])
            if j["password"] != j.get("password2"):
                raise ValueError("password mismatch")
            user.role_password = hash_password(user.role_name, j["password"]).decode(
                "utf-8"
            )

    for name in wanted_groups - current_groups:
        g.db_session.add(
            orm.RoleGroups(role_name=user.role_name, group_name=name, group_kind="role")
        )
    g.db_session.flush()

    return flask.jsonify(user.asdict())


@app.route("/json/users/<name>", methods=["DELETE"])
@admin_required
@transaction
def delete_user(name):
    result = g.db_session.execute(orm.Role.delete(name))
    if result.rowcount == 0:
        flask.abort(404, "No such user.")
    return flask.jsonify()
