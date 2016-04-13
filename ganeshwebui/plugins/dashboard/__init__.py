from os import path
import tornado.web
import json
from sqlalchemy.exc import *

from ganeshwebui.handlers.base import JsonHandler, BaseHandler
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
        (r"/server/(.*)/([0-9]{1,5})/dashboard", DashboardHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/dashboard", DashboardProxyHandler, handler_conf),
        (r"/js/dashboard/(.*)", tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
    ]
    return routes

class DashboardHandler(BaseHandler):

    def get_dashboard(self, agent_address, agent_port):
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
            if __name__ not in [plugin.plugin_name for plugin in instance.plugins]:
                raise GaneshError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.get_secure_cookie("ganesh_%s_%s" % (instance.agent_address, instance.agent_port))
            if not xsession:
                raise GaneshError(401, "Authentication cookie is missing.")

            dashboard_history = ganeshd_dashboard_history(self.ssl_ca_cert_file, instance.agent_address, instance.agent_port, xsession)
            if dashboard_history and isinstance(dashboard_history, list) and len(dashboard_history) > 0:
                last_data = dashboard_history[-1]
                history = json.dumps(dashboard_history)
            else:
                # If dashboard history is empty, let's try to get data from the live data source.
                last_data = ganeshd_dashboard_live(self.ssl_ca_cert_file, instance.agent_address, instance.agent_port, xsession)
                history = ''
            return HTMLAsyncResult(
                http_code = 200,
                template_file = 'dashboard.html',
                template_path = self.template_path,
                data = {
                    'nav': True,
                    'role': role,
                    'instance': instance,
                    'dashboard' : last_data,
                    'history': history,
                    'buffers_delta' : 0,
                    'readratio': (100 - last_data['hitratio']),
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
                    self.logger.error(".....")
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
        run_background(self.get_dashboard, self.async_callback, (agent_address, agent_port))

class DashboardProxyHandler(JsonHandler):

    def get_dashboard(self, agent_address, agent_port):
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
            if __name__ not in [plugin.plugin_name for plugin in instance.plugins]:
                raise GaneshError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise GaneshError(401, 'X-Session header missing')

            dashboard_data = ganeshd_dashboard(self.ssl_ca_cert_file, instance.agent_address, instance.agent_port, xsession)
            return JSONAsyncResult(http_code = 200, data = dashboard_data)
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
        run_background(self.get_dashboard, self.async_callback, (agent_address, agent_port))
