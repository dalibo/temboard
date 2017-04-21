import tornado.web
from time import sleep

from temboardui.handlers.base import BaseHandler, JsonHandler
from temboardui.temboardclient import (
    TemboardError,
    temboard_login,
    temboard_profile,
)
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.application import (
    gen_cookie,
    get_instance,
    get_role_by_auth,
    hash_password,
)
from temboardui.errors import TemboardUIError


class LogoutHandler(BaseHandler):
    def get(self):
        try:
            self.clear_cookie('temboard')
        except Exception:
            pass
        self.redirect('/home')


class LoginHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        run_background(self.get_login, self.async_callback)

    @tornado.web.asynchronous
    def post(self):
        run_background(self.post_login, self.async_callback)

    def get_login(self):
        role = None
        try:
            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
        except Exception as e:
            self.logger.exception(str(e))
        if role is not None:
            return HTMLAsyncResult(
                http_code=302,
                redirection='/home'
            )
        return HTMLAsyncResult(
            http_code=200,
            template_file='login.html',
            data={
                'nav': False
            }
        )

    def post_login(self):
        try:
            self.logger.info("Login.")
            p_role_name = self.get_argument('username')
            p_role_password = self.get_argument('password')
            role_hash_password = hash_password(p_role_name, p_role_password)

            self.start_db_session()
            role = get_role_by_auth(self.db_session, p_role_name,
                                    role_hash_password)
            self.logger.info("Role '%s' authentificated." % (role.role_name))
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            sleep(1)
            self.logger.info("Done.")
            redirection = self.get_secure_cookie('referer_uri') \
                if self.get_secure_cookie('referer_uri') is not None \
                else '/home'
            return HTMLAsyncResult(
                http_code=302,
                redirection=redirection,
                secure_cookie={
                    'name': 'temboard',
                    'content': gen_cookie(role.role_name,
                                          role_hash_password)})
        except (TemboardUIError, Exception) as e:
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            sleep(1)
            return HTMLAsyncResult(
                http_code=401,
                template_file='login.html',
                data={'nav': False, 'error': 'Wrong username/password.'})


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
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
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
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception as e:
                pass
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
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

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
                expires_days=0.5
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
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception as e:
                pass
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


class LoginJsonHandler(JsonHandler):
    def post_login(self):
        try:
            self.logger.info("Login (API).")
            post = tornado.escape.json_decode(self.request.body)
            p_role_name = post['username']
            p_role_password = post['password']
            role_hash_password = hash_password(p_role_name, p_role_password)

            self.start_db_session()
            role = get_role_by_auth(self.db_session, p_role_name,
                                    role_hash_password)
            self.logger.info("Role '%s' authentificated." % (role.role_name))
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            sleep(1)
            self.logger.info("Done.")

            return JSONAsyncResult(
                http_code=200,
                data={"message": "OK"},
                secure_cookie={
                    'name': 'temboard',
                    'content': gen_cookie(role.role_name, role_hash_password)
                })

        except (TemboardUIError, Exception) as e:
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            sleep(1)
            return JSONAsyncResult(
                http_code=401,
                data={"error": "Wrong username/password."})

    @tornado.web.asynchronous
    def post(self):
        run_background(self.post_login, self.async_callback)
