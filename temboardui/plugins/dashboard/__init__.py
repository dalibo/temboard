from os import path
import tornado.web
import json

from temboardui.handlers.base import JsonHandler, BaseHandler
from temboardui.temboardclient import (
    TemboardError,
    temboard_dashboard,
    temboard_dashboard_history,
    temboard_dashboard_live,
    temboard_profile,
)
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.errors import TemboardUIError
from temboardui.application import get_instance


def configuration(config):
    return {}


def get_routes(config):
    plugin_path = path.dirname(path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.temboard['ssl_ca_cert_file'],
        'template_path': plugin_path + "/templates"
    }
    routes = [
        (r"/server/(.*)/([0-9]{1,5})/dashboard", DashboardHandler,
         handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/dashboard", DashboardProxyHandler,
         handler_conf),
        (r"/js/dashboard/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


class DashboardHandler(BaseHandler):
    def get_dashboard(self, agent_address, agent_port):
        try:
            self.logger.info("Getting dashboard.")
            instance = None
            role = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if __name__ not in [
                    plugin.plugin_name for plugin in instance.plugins
            ]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.get_secure_cookie("temboard_%s_%s" %
                                              (instance.agent_address,
                                               instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")
            else:
                data_profile = temboard_profile(self.ssl_ca_cert_file,
                                                instance.agent_address,
                                                instance.agent_port,
                                                xsession)
                agent_username = data_profile['username']

            dashboard_history = temboard_dashboard_history(
                self.ssl_ca_cert_file, instance.agent_address,
                instance.agent_port, xsession)
            if dashboard_history and isinstance(
                    dashboard_history, list) and len(dashboard_history) > 0:
                last_data = dashboard_history[-1]
                history = json.dumps(dashboard_history)
            else:
                # If dashboard history is empty, let's try to get data from the
                # live data source.
                last_data = temboard_dashboard_live(
                    self.ssl_ca_cert_file, instance.agent_address,
                    instance.agent_port, xsession)
                history = ''
            self.logger.info("Done.")
            return HTMLAsyncResult(
                http_code=200,
                template_file='dashboard.html',
                template_path=self.template_path,
                data={
                    'nav': True,
                    'role': role,
                    'instance': instance,
                    'plugin': 'dashboard',
                    'dashboard': last_data,
                    'history': history,
                    'buffers_delta': 0,
                    'readratio': (100 - last_data['hitratio']),
                    'xsession': xsession,
                    'agent_username': agent_username,
                })
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.expunge_all()
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
                    isinstance(e, TemboardError)):
                if e.code == 401:
                    return HTMLAsyncResult(
                        http_code=401,
                        redirection="/server/%s/%s/login" % (agent_address,
                                                             agent_port))
                elif e.code == 302:
                    return HTMLAsyncResult(http_code=401, redirection="/login")
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                http_code=code,
                template_file='error.html',
                data={
                    'nav': True,
                    'role': role,
                    'instance': instance,
                    'code': e.code,
                    'error': e.message
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_dashboard, self.async_callback, (agent_address,
                                                                 agent_port))


class DashboardProxyHandler(JsonHandler):
    def get_dashboard(self, agent_address, agent_port):
        try:
            self.logger.info("Getting dashboard (proxy).")
            role = None
            instance = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")
            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if __name__ not in [
                    plugin.plugin_name for plugin in instance.plugins
            ]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise TemboardUIError(401, 'X-Session header missing')

            dashboard_data = temboard_dashboard(self.ssl_ca_cert_file,
                                                instance.agent_address,
                                                instance.agent_port, xsession)
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=dashboard_data)
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
                    isinstance(e, TemboardError)):
                return JSONAsyncResult(
                    http_code=e.code, data={'error': e.message})
            else:
                return JSONAsyncResult(
                    http_code=500, data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_dashboard, self.async_callback, (agent_address,
                                                                 agent_port))
