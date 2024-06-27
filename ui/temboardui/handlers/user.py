import logging
from time import sleep

from ..application import gen_cookie, get_role_by_auth, hash_password
from ..errors import TemboardUIError
from ..web.tornado import Redirect, Response, anonymous_allowed, app, render_template

logger = logging.getLogger(__name__)


@app.route("/logout")
def logout(request):
    request.handler.clear_cookie("temboard")
    # Redirect to /home so that /login referer is /home, not logout.
    return Redirect("/home")


def login_common(db_session, rolename, password):
    # Common logic between json and HTML login.
    passhash = hash_password(rolename, password).decode("utf-8")
    role = get_role_by_auth(db_session, rolename, passhash)
    logger.info("Role '%s' authentificated.", role.role_name)
    return dict(temboard=gen_cookie(role.role_name, passhash))


@app.route("/login", methods=["GET", "POST"])
@anonymous_allowed
def login(request):
    if "GET" == request.method:
        if request.current_user is None:
            return render_template("login.html", nav=False)
        else:
            return Redirect("/home")
    else:
        # Ensure request take at least one second to mitigate dictionnaries
        # attacks.
        sleep(1)
        try:
            rolename = request.handler.get_argument("username")
            password = request.handler.get_argument("password")
            cookies = login_common(request.db_session, rolename, password)
            referer = request.handler.get_secure_cookie("referer_uri")
            return Redirect(referer or "/home", secure_cookies=cookies)
        except TemboardUIError as e:
            logger.error("Login failed: %s", e)
            response = render_template(
                "login.html", nav=False, error="Wrong username/password."
            )
            response.status_code = 401
            return response


@app.route(r"/json/login", methods=["POST"])
@anonymous_allowed
def json_login(request):
    username = request.json["username"]
    password = request.json["password"]

    # Mitigate dictionnaries attacks.
    sleep(1)

    try:
        cookies = login_common(request.db_session, username, password)
        return Response(body={"message": "OK"}, secure_cookies=cookies)
    except TemboardUIError as e:
        logger.error("Login failed: %s", e)
        return Response(status_code=401, body={"error": "Wrong username/password."})
