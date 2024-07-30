import logging
from time import sleep

from flask import current_app as app
from flask import g, jsonify, make_response, redirect, render_template, request
from tornado.web import create_signed_value

from temboardui.application import gen_cookie, get_role_by_auth, hash_password
from temboardui.errors import TemboardUIError

from ..flask import anonymous_allowed

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
    return render_template("login.html", nav=False, vitejs=app.vitejs)


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
