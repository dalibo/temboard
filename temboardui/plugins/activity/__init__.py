from os import path
import tornado.web

from temboardui.handlers.base import JsonHandler, BaseHandler
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.errors import TemboardUIError
from temboardui.temboardclient import (
    temboard_activity,
    temboard_activity_blocking,
    temboard_activity_kill,
    temboard_activity_waiting,
    temboard_profile,
)


def configuration(config):
    return {}


def get_routes(config):
    plugin_path = path.dirname(path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.temboard['ssl_ca_cert_file'],
        'template_path': plugin_path + "/templates"
    }
    routes = [
        (r"/server/(.*)/([0-9]{1,5})/activity/(running|blocking|waiting)",
         ActivityHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity",
         ActivityProxyHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/(blocking|waiting)$",
         ActivityProxyHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/kill", ActivityKillProxyHandler,
         handler_conf),
        (r"/js/activity/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


class ActivityHandler(BaseHandler):

    @BaseHandler.catch_errors
    def get_activity(self, agent_address, agent_port, mode):
        self.logger.info("Getting activity.")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.get_secure_cookie("temboard_%s_%s" %
                                          (agent_address, agent_port))
        if not xsession:
            raise TemboardUIError(401, "Authentication cookie is missing.")
        else:
            data_profile = temboard_profile(self.ssl_ca_cert_file,
                                            agent_address,
                                            agent_port,
                                            xsession)
            agent_username = data_profile['username']

        self.logger.info("Done.")
        return HTMLAsyncResult(
            http_code=200,
            template_path=self.template_path,
            template_file='activity.html',
            data={
                'nav': True,
                'role': self.current_user,
                'instance': self.instance,
                'plugin': __name__,
                'mode': mode,
                'xsession': xsession,
                'agent_username': agent_username,
            })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, mode):
        run_background(self.get_activity, self.async_callback,
                       (agent_address, agent_port, mode))


class ActivityProxyHandler(JsonHandler):

    @JsonHandler.catch_errors
    def get_activity(self, agent_address, agent_port, mode):
        self.logger.info("Getting activity (proxy).")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise TemboardUIError(401, 'X-Session header missing')

        # Load activity.
        if mode == 'waiting':
            data_activity = temboard_activity_waiting(
                self.ssl_ca_cert_file, agent_address, agent_port, xsession)
        elif mode == 'blocking':
            data_activity = temboard_activity_blocking(
                self.ssl_ca_cert_file, agent_address, agent_port, xsession)
        else:
            data_activity = temboard_activity(
                self.ssl_ca_cert_file, agent_address, agent_port, xsession)
        self.logger.info("Done.")
        return JSONAsyncResult(http_code=200, data=data_activity)

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, mode='running'):
        run_background(self.get_activity, self.async_callback,
                       (agent_address, agent_port, mode))


class ActivityKillProxyHandler(JsonHandler):

    @JsonHandler.catch_errors
    def post_kill(self, agent_address, agent_port):
        self.logger.info("Posting terminate backend.")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise TemboardUIError(401, 'X-Session header missing')

        self.logger.debug(tornado.escape.json_decode(self.request.body))
        data_kill = temboard_activity_kill(
            self.ssl_ca_cert_file, agent_address, agent_port, xsession,
            tornado.escape.json_decode(self.request.body))
        self.logger.info("Done.")
        return JSONAsyncResult(http_code=200, data=data_kill)

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_kill, self.async_callback, (agent_address,
                                                             agent_port))
