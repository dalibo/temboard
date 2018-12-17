import logging
import tornado.web
from time import sleep

from temboardui.handlers.base import BaseHandler
from temboardui.temboardclient import (
    TemboardError,
    temboard_login,
    temboard_profile,
)
from temboardui.async import (
    HTMLAsyncResult,
    run_background,
)
from temboardui.application import (
    gen_cookie,
    get_instance,
    get_role_by_auth,
    hash_password,
)
from temboardui.errors import TemboardUIError
from ..web import (
    Redirect,
    Response,
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


class AgentLoginHandler(BaseHandler):
    """ Login Handler """

    def get_login(self, agent_address, agent_port):
        try:
            instance = None
            role = None
            agent_username = None
            self.start_db_session()
            try:
                self.load_auth_cookie()
                role = self.current_user
            except Exception as e:
                pass
            if role is None:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" % (instance.agent_address,
                                    instance.agent_port))
            if xsession:
                try:
                    data_profile = temboard_profile(self.ssl_ca_cert_file,
                                                    instance.agent_address,
                                                    instance.agent_port,
                                                    xsession)
                    agent_username = data_profile['username']
                    self.logger.error(agent_username)
                except Exception as e:
                    self.logger.exception(str(e))

            return HTMLAsyncResult(
                http_code=200,
                template_file='agent-login.html',
                data={
                    'nav': True,
                    'instance': instance,
                    'role': role,
                    'username': agent_username
                })
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                if e.code == 302:
                    return HTMLAsyncResult(http_code=401, redirection="/login")
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                http_code=code,
                template_file='error.html',
                data={
                    'nav': True,
                    'instance': instance,
                    'code': str(e.code),
                    'message': str(e.message)
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_login, self.async_callback,
                       (agent_address, agent_port))

    def post_login(self, agent_address, agent_port):
        try:
            self.logger.info("Posting to agent login.")
            instance = None
            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)

            xsession = temboard_login(
                        self.ssl_ca_cert_file,
                        instance.agent_address,
                        instance.agent_port,
                        self.get_argument("username"),
                        self.get_argument("password"))

            self.set_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port),
                xsession,
                expires_days=30
            )
            self.logger.info("Done.")
            redirection = self.get_secure_cookie('referer_uri') \
                if self.get_secure_cookie('referer_uri') is not None \
                else "/server/%s/%s/dashboard" % (instance.agent_address,
                                                  instance.agent_port)
            return HTMLAsyncResult(http_code=302,
                                   redirection=redirection)
        except (TemboardError, TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            return HTMLAsyncResult(
                    http_code=200,
                    template_file='agent-login.html',
                    data={
                        'nav': True,
                        'error': e.message,
                        'instance': instance,
                        'username': None
                    })

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_login, self.async_callback,
                       (agent_address, agent_port))
