import tornado.web
from time import sleep
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import *

from ganeshwebui.handlers.base import BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *
from ganeshwebui.async import *
from ganeshwebui.application import hash_password, get_role_by_auth, gen_cookie, get_instance
from ganeshwebui.errors import GaneshError


class LogoutHandler(BaseHandler):
    def get(self):
        try:
            self.clear_cookie('ganesh')
        except Exception as e:
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
        return HTMLAsyncResult(
            http_code = 200,
            template_file = 'login.html',
            data = { 'nav': False })

    def post_login(self):
        try:
            p_role_name = self.get_argument('username')
            p_role_password = self.get_argument('password')
            role_hash_password = hash_password(p_role_name, p_role_password)

            self.start_db_session()
            role = get_role_by_auth(self.db_session, p_role_name, role_hash_password)
            self.logger.info("Role '%s' authentificated." % (role.role_name))
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            sleep(1)

            return HTMLAsyncResult(
                http_code = 302,
                redirection = '/home',
                secure_cookie = { 'name': 'ganesh', 'content': gen_cookie(role.role_name, role_hash_password)})
        except (GaneshError, Exception) as e:
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            self.logger.error(e.message)
            sleep(1)
            return HTMLAsyncResult(
                http_code = 401,
                template_file = 'login.html',
                data = { 'nav': False , 'error': 'Wrong username/password.'})

class AgentLoginHandler(BaseHandler):
    """ Login Handler """

    def get_login(self, agent_address, agent_port):
        try:
            instance = None
            #self.load_auth_cookie()
            self.start_db_session()

            instance = get_instance(self.db_session, agent_address, agent_port)
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            return HTMLAsyncResult(
                http_code = 200,
                template_file = 'agent-login.html',
                data = {
                    'nav': True,
                    'instance': instance,
                    'role': None
                })
        except (GaneshError, GaneshdError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception as e:
                pass
            if (isinstance(e, GaneshError) or isinstance(e, GaneshdError)):
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                        http_code = code,
                        template_file = 'error.html',
                        data = {
                            'nav': True,
                            'instance': instance,
                            'code': str(e.code),
                            'message': str(e.message)
                        })


    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_login, self.async_callback, (agent_address, agent_port))

    def post_login(self, agent_address, agent_port):
        try:
            instance = None
            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise GaneshError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = ganeshd_login(
                        self.ssl_ca_cert_file,
                        instance.agent_address,
                        instance.agent_port,
                        self.get_argument("username"),
                        self.get_argument("password"))

            self.set_secure_cookie("ganesh_%s_%s" % (instance.agent_address, instance.agent_port), xsession)

            return HTMLAsyncResult(http_code = 302, redirection = "/server/%s/%s/dashboard" % (instance.agent_address, instance.agent_port))
        except (GaneshdError, GaneshError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.rollback()
                self.db_session.close()
            except Exception as e:
                pass
            return HTMLAsyncResult(
                    http_code = 200,
                    template_file = 'agent-login.html',
                    data = {
                        'nav': True,
                        'error': e.message,
                        'instance': instance
                    })

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_login, self.async_callback, (agent_address, agent_port))
