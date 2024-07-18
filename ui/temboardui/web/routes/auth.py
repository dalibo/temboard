import logging
from time import sleep

from flask import current_app as app
from flask import g, jsonify, make_response, redirect, render_template, request
from tornado.web import create_signed_value, decode_signed_value

from temboardui.application import gen_cookie, get_role_by_auth, hash_password
from temboardui.errors import TemboardUIError

from ..flask import anonymous_allowed

logger = logging.getLogger(__name__)


@app.route("/logout")
def logout():
    # Redirect to /home so that /login referer is /home, not logout.
    response = make_response(redirect("/home"))
    response.delete_cookie("temboard")
    return response


@app.route("/login", methods=["GET", "POST"])
@anonymous_allowed
def login():
    if request.method == "GET":
        if g.current_user is None:
            return render_template("login.html", nav=False, vitejs=app.vitejs)
        else:
            return redirect("/home")
    else:
        # Ensure request take at least one second to mitigate dictionnaries
        # attacks.
        sleep(1)
        try:
            rolename = request.form.get("username")
            password = request.form.get("password")
            referer = decode_signed_value(
                app.temboard.config.temboard.cookie_secret,
                "referer_uri",
                request.cookies["referer_uri"],
            )
            if referer:
                referer = referer.decode("utf-8")
            response = make_response(redirect(referer or "/home"))
            login_common(g.db_session, rolename, password, response)
        except TemboardUIError as e:
            logger.error("Login failed: %s", e)
            response = render_template(
                "login.html", nav=False, error="Wrong username/password."
            )
            response.status_code = 401

        return response


@app.route(r"/json/login", methods=["POST"])
@anonymous_allowed
def json_login():
    username = request.json["username"]
    password = request.json["password"]

    response = make_response(jsonify({"message": "OK"}))
    try:
        login_common(g.db_session, username, password, response)
    except TemboardUIError as e:
        logger.error("Login failed: %s", e)
        response = make_response(jsonify({"error": "Wrong username/password."}))
        response.status_code = 401
        # Mitigate dictionnaries attacks.
        sleep(1)
    return response


def login_common(db_session, rolename, password, response):
    # Common logic between json and HTML login.
    passhash = hash_password(rolename, password).decode("utf-8")
    role = get_role_by_auth(db_session, rolename, passhash)
    logger.info("Role '%s' authentificated.", role.role_name)
    secret_cookie = create_signed_value(
        app.temboard.config.temboard.cookie_secret,
        "temboard",
        gen_cookie(role.role_name, passhash),
    )
    response.set_cookie("temboard", secret_cookie.decode(), secure=True)
