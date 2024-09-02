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


@app.route("/json/users")
@admin_required
def get_users():
    return jsonify([u.asdict() for u in orm.Role.all().with_session(g.db_session)])


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
    if user is None:
        user = orm.Role.get(name).with_session(g.db_session).one_or_none()
    if user is None:
        flask.abort(404, "No such user.")

    j = request.json
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


@app.route("/json/groups/<path:groupname>/members/<username>")
@admin_required
def get_group_membership(groupname, username):
    row = g.db_session.execute(orm.Group.select_membership(groupname, username)).first()
    if not row:
        flask.abort(404, "No such membership.")

    return flask.jsonify({k: getattr(row, k) for k in row.keys()})


@app.route("/json/groups/<path:groupname>/members", methods=["POST"])
@admin_required
@transaction
def post_group_membership(groupname):
    gr = orm.Group.get(groupname).with_session(g.db_session).one_or_none()
    if not gr:
        flask.abort(404, "No such group.")

    g.db_session.execute(gr.insert_member(request.json["username"]))
    return flask.jsonify(
        username=request.json["username"], groupname=gr.name, profile=gr.description
    )


@app.route("/json/groups/<path:groupname>/members/<username>", methods=["DELETE"])
@admin_required
@transaction
def delete_group_membership(groupname, username):
    """Remove a user from a group."""
    result = g.db_session.execute(orm.Group.delete_member(groupname, username))
    if not result.rowcount:
        flask.abort(404, "No such membership.")

    return flask.jsonify()
