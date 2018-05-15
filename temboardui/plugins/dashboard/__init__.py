from os import path
import tornado.web
import json

from temboardui.handlers.base import JsonHandler, BaseHandler
from temboardui.temboardclient import (
    TemboardError,
    temboard_dashboard,
    temboard_dashboard_config,
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

    @BaseHandler.catch_errors
    def get_dashboard(self, agent_address, agent_port):
        self.logger.info("Getting dashboard.")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.get_secure_cookie("temboard_%s_%s" %
                                          (agent_address, agent_port))
        if not xsession:
            raise TemboardUIError(401, "Authentication cookie is missing.")
        else:
            data_profile = temboard_profile(self.ssl_ca_cert_file,
                                            agent_address, agent_port,
                                            xsession)
            agent_username = data_profile['username']

        try:
            config = temboard_dashboard_config(
                self.ssl_ca_cert_file, agent_address, agent_port, xsession)
        except TemboardError as e:
            # Agent may not be able to send config (old agent)
            # Use a default one
            if e.code == 404:
                config = {
                    'history_length': 150,
                    'scheduler_interval': 2
                }
            else:
                raise e

        dashboard_history = temboard_dashboard_history(
            self.ssl_ca_cert_file, agent_address, agent_port, xsession)
        if dashboard_history and isinstance(
                dashboard_history, list) and len(dashboard_history) > 0:
            last_data = dashboard_history[-1]
            history = json.dumps(dashboard_history)
        else:
            # If dashboard history is empty, let's try to get data from the
            # live data source.
            last_data = temboard_dashboard_live(
                self.ssl_ca_cert_file, agent_address, agent_port, xsession)
            history = ''
        self.logger.info("Done.")
        return HTMLAsyncResult(
            http_code=200,
            template_file='dashboard.html',
            template_path=self.template_path,
            data={
                'nav': True,
                'role': self.current_user,
                'instance': self.instance,
                'plugin': __name__,
                'dashboard': last_data,
                'config': json.dumps(config),
                'history': history,
                'buffers_delta': 0,
                'readratio': (100 - last_data['hitratio']),
                'xsession': xsession,
                'agent_username': agent_username,
            })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_dashboard, self.async_callback, (agent_address,
                                                                 agent_port))


class DashboardProxyHandler(JsonHandler):

    @JsonHandler.catch_errors
    def get_dashboard(self, agent_address, agent_port):
        self.logger.info("Getting dashboard (proxy).")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise TemboardUIError(401, 'X-Session header missing')

        dashboard_data = temboard_dashboard(self.ssl_ca_cert_file,
                                            agent_address,
                                            agent_port, xsession)
        self.logger.info("Done.")
        return JSONAsyncResult(http_code=200, data=dashboard_data)

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_dashboard, self.async_callback, (agent_address,
                                                                 agent_port))
