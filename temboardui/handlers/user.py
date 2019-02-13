import logging
from time import sleep

import tornado.web

from ..application import (
    gen_cookie,
    get_role_by_auth,
    hash_password,
)
from ..errors import TemboardUIError
from ..web import (
    HTTPError,
    Redirect,
    Response,
    anonymous_allowed,
    app,
    render_template,
)


logger = logging.getLogger(__name__)


@app.route('/logout')
def logout(request):
    request.handler.clear_cookie('temboard')
    # Redirect to /home so that /login referer is /home, not logout.
    return Redirect('/home')


def login_common(db_session, rolename, password):
    # Common logic between json and HTML login.
    passhash = hash_password(rolename, password)
    role = get_role_by_auth(db_session, rolename, passhash)
    logger.info(u"Role '%s' authentificated.", role.role_name)
    return dict(temboard=gen_cookie(role.role_name, passhash))


@app.route('/login', methods=['GET', 'POST'])
@anonymous_allowed
def login(request):
    if 'GET' == request.method:
        if request.current_user is None:
            return render_template('login.html', nav=False)
        else:
            return Redirect('/home')
    else:
        # Ensure request take at least one second to mitigate dictionnaries
        # attacks.
        sleep(1)
        try:
            rolename = request.handler.get_argument('username')
            password = request.handler.get_argument('password')
            cookies = login_common(request.db_session, rolename, password)
            referer = request.handler.get_secure_cookie('referer_uri')
            return Redirect(referer or '/home', secure_cookies=cookies)
        except TemboardUIError as e:
            logger.error(u"Login failed: %s", e)
            response = render_template(
                'login.html',
                nav=False,
                error=u"Wrong username/password.",
            )
            response.status_code = 401
            return response


@app.route(r'/json/login', methods=['POST'])
@anonymous_allowed
def json_login(request):
    # Mitigate dictionnaries attacks.
    sleep(1)
    try:
        post = tornado.escape.json_decode(request.body)
        username = post['username']
        password = post['password']
        cookies = login_common(request.db_session, username, password)
        return Response(
            body={"message": "OK"},
            secure_cookies=cookies,
        )
    except TemboardUIError as e:
        logger.error(u"Login failed: %s", e)
        return Response(
            status_code=401,
            body={"error": "Wrong username/password."},
        )


@app.instance_route(r'/login', methods=['GET', 'POST'])
def agent_login(request):
    error = None
    username = None
    if 'GET' == request.method:
        if not request.current_user:
            return Redirect('/login')

        redirect_to = request.handler.get_query_argument('redirect_to', None)
        if redirect_to:
            request.handler.set_secure_cookie('referer_uri', redirect_to,
                                              expires_days=30)
        if request.instance.xsession:
            try:
                profile = request.instance.get_profile()
            except Exception as e:
                logger.debug("Failed to get profile: %s.", e)
                logger.debug("Is X-Session valid? Showing login form.")
            else:
                username = profile['username']
    else:
        creds = dict(
            username=request.handler.get_argument('username'),
            password=request.handler.get_argument('password'),
        )
        try:
            response = request.instance.post("/login", body=creds)
            xsession = response['session']
        except HTTPError as e:
            error = e.log_message
        else:
            cookies = {request.instance.cookie_name: xsession}
            location = request.handler.get_secure_cookie('referer_uri')
            if not location:
                location = request.instance.format_url('/dashboard')
            return Redirect(location, secure_cookies=cookies)

    return render_template(
        'agent-login.html',
        nav=True, instance=request.instance, username=username,
        role=request.current_user,
        error=error,
    )
