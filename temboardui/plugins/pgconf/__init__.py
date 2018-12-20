from os import path
import tornado.web
import tornado.escape

from temboardui.handlers.base import JsonHandler, BaseHandler
from temboardui.temboardclient import (
    TemboardError,
    temboard_get_configuration,
    temboard_get_configuration_categories,
    temboard_get_configuration_status,
    temboard_post_configuration,
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
        'template_path':  plugin_path + "/templates"
    }
    routes = [
        (
            r"/server/(.*)/([0-9]{1,5})/pgconf/configuration$",
            ConfigurationHandler,
            handler_conf
        ),
        (
            r"/server/(.*)/([0-9]{1,5})/pgconf/configuration/category/(.+)$",
            ConfigurationHandler,
            handler_conf
        ),
        (
            r"/proxy/(.*)/([0-9]{1,5})/pgconf/configuration",
            ConfigurationProxyHandler,
            handler_conf
        ),
        (
            r"/js/pgconf/(.*)",
            tornado.web.StaticFileHandler,
            {'path': plugin_path + "/static/js"}
        ),
        (
            r"/css/pgconf/(.*)",
            tornado.web.StaticFileHandler,
            {'path': plugin_path + "/static/css"}
        ),
    ]
    return routes


class ConfigurationHandler(BaseHandler):
    """  HTML handler """

    @BaseHandler.catch_errors
    def get_configuration(self, agent_address, agent_port, category=None):
        self.logger.info("Getting configuration.")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.get_secure_cookie(
            "temboard_%s_%s" %
            (agent_address, agent_port))
        if not xsession:
            raise TemboardUIError(401, "Authentication cookie is missing.")
        else:
            data_profile = temboard_profile(self.ssl_ca_cert_file,
                                            agent_address,
                                            agent_port,
                                            xsession)
            agent_username = data_profile['username']

        configuration_status = temboard_get_configuration_status(
                                    self.ssl_ca_cert_file,
                                    agent_address,
                                    agent_port,
                                    xsession)
        configuration_cat = temboard_get_configuration_categories(
                                    self.ssl_ca_cert_file,
                                    agent_address,
                                    agent_port,
                                    xsession)
        query_filter = self.get_argument('filter', None, True)
        if category is None:
            category = tornado.escape.url_escape(
                configuration_cat['categories'][0])
        url = tornado.escape.url_escape(
            tornado.escape.url_unescape(category))
        configuration_data = temboard_get_configuration(
            self.ssl_ca_cert_file,
            agent_address,
            agent_port,
            xsession,
            url,
            query_filter)
        self.logger.info("Done.")

        return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='configuration.html',
                data={
                    'nav': True,
                    'role': self.current_user,
                    'instance': self.instance,
                    'plugin': __name__,
                    'data': configuration_data,
                    'xsession': xsession,
                    'agent_username': agent_username,
                    'current_cat': tornado.escape.url_unescape(category),
                    'configuration_categories': configuration_cat,
                    'configuration_status': configuration_status,
                    'query_filter': query_filter
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, category=None):
        run_background(self.get_configuration, self.async_callback,
                       (agent_address, agent_port, category))

    @BaseHandler.catch_errors
    def post_configuration(self, agent_address, agent_port, category=None):
        self.logger.info("Posting configuration.")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.get_secure_cookie(
            "temboard_%s_%s" %
            (agent_address, agent_port))
        if not xsession:
            raise TemboardUIError(401, "Authentication cookie is missing.")

        query_filter = self.get_argument('filter', None, True)
        error_code = None
        error_message = None
        post_settings = self.request.arguments
        ret_post = None
        settings = {'settings': []}
        for setting_name, setting_value in post_settings.iteritems():
            # 'filter' is not a setting, just ignore it.
            if setting_name == 'filter':
                continue
            settings['settings'].append({'name': setting_name,
                                         'setting': setting_value[0]})
        try:
            # Try to send settings to the agent.
            ret_post = temboard_post_configuration(
                            self.ssl_ca_cert_file,
                            agent_address,
                            agent_port,
                            xsession,
                            settings)
        except TemboardError as e:
            error_code = e.code
            error_message = e.message
        # Get PostgreSQL configuration status: needs restart or is fine.
        configuration_status = temboard_get_configuration_status(
                                    self.ssl_ca_cert_file,
                                    agent_address,
                                    agent_port,
                                    xsession)
        # Load settings categories.
        configuration_cat = temboard_get_configuration_categories(
                                self.ssl_ca_cert_file,
                                agent_address,
                                agent_port,
                                xsession)
        if category is None:
            category = tornado.escape.url_escape(
                configuration_cat['categories'][0])
        # Load settings depending on the current category or the filter
        # value.
        url = tornado.escape.url_escape(
            tornado.escape.url_unescape(category))
        configuration_data = temboard_get_configuration(
                                self.ssl_ca_cert_file,
                                agent_address,
                                agent_port,
                                xsession,
                                url,
                                query_filter)
        self.logger.info("Done.")
        return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='configuration.html',
                data={
                    'nav': True,
                    'role': self.current_user,
                    'instance': self.instance,
                    'plugin': __name__,
                    'data': configuration_data,
                    'xsession': xsession,
                    'current_cat': tornado.escape.url_unescape(category),
                    'configuration_categories': configuration_cat,
                    'configuration_status': configuration_status,
                    'error_code': error_code,
                    'error_message': error_message,
                    'ret_post': ret_post,
                    'query_filter': query_filter
                })

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port, category=None):
        run_background(self.post_configuration, self.async_callback,
                       (agent_address, agent_port, category))


"""
Proxy Handlers
"""


class ConfigurationProxyHandler(JsonHandler):
    """ /pgconf/configuration JSON handler """

    @JsonHandler.catch_errors
    def post_configuration(self, agent_address, agent_port):
        self.logger.info("Posting configuration (proxy).")

        self.setUp(agent_address, agent_port)
        self.check_active_plugin(__name__)

        xsession = self.get_secure_cookie(
            "temboard_%s_%s" %
            (agent_address, agent_port))
        if not xsession:
            raise TemboardUIError(401, "Authentication cookie is missing.")

        data = temboard_post_configuration(
                    self.ssl_ca_cert_file,
                    agent_address,
                    agent_port,
                    xsession,
                    tornado.escape.json_decode(self.request.body))
        self.logger.info("Done.")
        return JSONAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_configuration, self.async_callback,
                       (agent_address, agent_port))
