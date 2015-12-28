from os import path
import tornado.web
from sqlalchemy.exc import *

from ganeshwebui.handlers.base import JsonHandler, BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *
from ganeshwebui.async import *
from ganeshwebui.errors import GaneshError
from ganeshwebui.application import get_instance
from ganeshwebui.ganeshdclient import GaneshdError

def configuration(config):
    return {}

def get_routes(config):
    plugin_path = path.dirname(path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.ganesh['ssl_ca_cert_file'],
        'template_path':  plugin_path + "/templates"
    }
    routes = [
        (r"/server/(.*)/([0-9]{1,5})/activity", ActivityHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity", ActivityProxyHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/kill", ActivityKillProxyHandler, handler_conf),
        (r"/js/activity/(.*)", tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
    ]
    return routes

class ActivityHandler(BaseHandler):
    def get_activity(self, agent_address, agent_port):
        try:
            instance = None
            role = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise GaneshError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise GaneshError(404, "Instance not found.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie("ganesh_%s_%s" % (instance.agent_address, instance.agent_port))
            if not xsession:
                raise GaneshError(401, "Authentication cookie is missing.")

            # Load activity.
            activity_data = ganeshd_activity(self.ssl_ca_cert_file, instance.agent_address, instance.agent_port, xsession)
            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'activity.html',
                    data = {
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'activities': activity_data,
                        'xsession': xsession
                    })
        except (GaneshError, GaneshdError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.expunge_all()
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, GaneshError) or isinstance(e, GaneshdError)):
                if e.code == 401:
                    return HTMLAsyncResult(http_code = 401, redirection = "/server/%s/%s/login" % (agent_address, agent_port))
                elif e.code == 302:
                    return HTMLAsyncResult(http_code = 401, redirection = "/login")
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                        http_code = code,
                        template_file = 'error.html',
                        data = {
                            'nav': True,
                            'role': role,
                            'instance': instance,
                            'code': e.code,
                            'error': e.message
                        })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_activity, self.async_callback, (agent_address, agent_port))

class ActivityProxyHandler(JsonHandler):
    def get_activity(self, agent_address, agent_port):
        try:
            role = None
            instance = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise GaneshError(302, "Current role unknown.")
            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise GaneshError(404, "Instance not found.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise GaneshError(401, 'X-Session header missing')

            data_activity = ganeshd_activity(self.ssl_ca_cert_file, instance.agent_address, instance.agent_port, xsession)
            return JSONAsyncResult(http_code = 200, data = data_activity)
        except (GaneshError, GaneshdError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, GaneshError) or isinstance(e, GaneshdError)):
                return JSONAsyncResult(http_code = e.code, data = {'error': e.message})
            else:
                return JSONAsyncResult(http_code = 500, data = {'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_activity, self.async_callback, (agent_address, agent_port))

class ActivityKillProxyHandler(JsonHandler):
    def post_kill(self, agent_address, agent_port):
        try:
            self.logger.error(self.request.body)
            role = None
            instance = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise GaneshError(302, "Current role unknown.")
            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise GaneshError(404, "Instance not found.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise GaneshError(401, 'X-Session header missing')

            data_kill = ganeshd_activity_kill(self.ssl_ca_cert_file, instance.agent_address, instance.agent_port, xsession, tornado.escape.json_decode(self.request.body))
            return JSONAsyncResult(http_code = 200, data = data_kill)
        except (GaneshError, GaneshdError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, GaneshError) or isinstance(e, GaneshdError)):
                return JSONAsyncResult(http_code = e.code, data = {'error': e.message})
            else:
                return JSONAsyncResult(http_code = 500, data = {'error': e.message})

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_kill, self.async_callback, (agent_address, agent_port))
