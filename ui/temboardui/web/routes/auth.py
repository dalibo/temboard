import logging
from time import sleep

import flask
from flask import current_app as app
from flask import (
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from itsdangerous import SignatureExpired
from temboardtoolkit import validators
from temboardui.application import (
    gen_cookie,
    get_reset_token_serializer,
    get_role_by_auth,
    hash_password,
    send_mail,
)
from temboardui.errors import TemboardUIError
from tornado.web import create_signed_value

from ...model import orm
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
    response.set_cookie(
        "temboard",
        secret_cookie.decode(),
        secure=True,
        max_age=app.temboard.config.temboard.cookie_timeout,
    )
    return response


@app.route("/reset-password", methods=["GET"])
@anonymous_allowed
def reset_password():
    return render_template("reset-password.html", headerbar=False)


@app.route("/json/reset-password", methods=["POST"])
@anonymous_allowed
def json_reset_pwd():
    if request.method == "POST":
        data = request.json
        identifier = data.get("identifier")

        role = (
            g.db_session.query(orm.Role)
            .filter(
                (orm.Role.role_name == identifier) | (orm.Role.role_email == identifier)
            )
            .first()
        )

        if role:
            serializer = get_reset_token_serializer()
            token = serializer.dumps(role.role_name, salt="pwd-reset")
            link = url_for("reset_token", token=token, _external=True)
            content = f"""
            Hello {role.role_name},

            A password reset for your temBoard account has been requested.

            Click the link below to reset your password (valid for 30 minutes):
            {link}

            If you did not request this, you can safely ignore this email.
            """

            try:
                send_mail(
                    host=app.temboard.config.notifications.smtp_host,
                    port=app.temboard.config.notifications.smtp_port,
                    subject="temBoard password reset",
                    content=content,
                    emails=[role.role_email],
                    tls=getattr(app.temboard.config.notifications, "smtp_tls", False),
                    login=getattr(
                        app.temboard.config.notifications, "smtp_login", None
                    ),
                    password=getattr(
                        app.temboard.config.notifications, "smtp_password", None
                    ),
                    from_addr=app.temboard.config.notifications.smtp_from_addr,
                )

            except TemboardUIError as e:
                logger.error("Failed to send email: %s", e)

            flash("A password reset link has been sent to your email.", "success")
            return jsonify()
        else:
            return jsonify({"error": "Invalid role or email."}), 400


def get_role_name_for_token(token):
    serializer = get_reset_token_serializer()

    try:
        role_name = serializer.loads(token, salt="pwd-reset", max_age=1800)
    except SignatureExpired:
        flash("Your reset link has expired. Please request a new one.", "error")
        raise ValueError

    return role_name


@app.route("/reset-password/<token>", methods=["GET"])
@anonymous_allowed
def reset_token(token):
    try:
        get_role_name_for_token(token)
    except ValueError:
        return redirect(url_for("reset_password"))

    return render_template("reset-password-form.html", token=token, headerbar=False)


@app.route("/json/reset-password/<token>", methods=["POST"])
@anonymous_allowed
def json_reset_password(token):
    try:
        role_name = get_role_name_for_token(token)
    except ValueError:
        # Possible improvement : use redirect with fetch on the client side (JS)
        return jsonify({"redirectUrl": url_for("reset_password")}), 400

    role = g.db_session.query(orm.Role).filter_by(role_name=role_name).first()
    if not role:
        return jsonify({"error": "User not found."}), 404

    data = request.json
    password = data.get("password")
    confirm = data.get("confirm")

    try:
        with validating():
            validators.password(password)
            if password != confirm:
                raise ValueError("Passwords do not match.")

            role.role_password = hash_password(role.role_name, password).decode("utf-8")
            g.db_session.commit()

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    flash("Your password has been successfully reset.", "success")
    return jsonify()


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
