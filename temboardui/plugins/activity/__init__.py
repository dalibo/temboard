from os import path
import tornado.web

from temboardui.handlers.base import JsonHandler, BaseHandler
from temboardui.async import (
    HTMLAsyncResult,
    JSONAsyncResult,
    run_background,
)
from temboardui.errors import TemboardUIError
from temboardui.application import get_instance
from temboardui.temboardclient import (
    TemboardError,
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
        (r"/server/(.*)/([0-9]{1,5})/activity/running", ActivityHandler,
         handler_conf),
        (r"/server/(.*)/([0-9]{1,5})/activity/(blocking|waiting)$",
         ActivityWBHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity", ActivityProxyHandler,
         handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/(blocking|waiting)$",
         ActivityWBProxyHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/kill", ActivityKillProxyHandler,
         handler_conf),
        (r"/js/activity/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


class ActivityHandler(BaseHandler):
    def get_activity(self, agent_address, agent_port):
        try:
            self.logger.info("Getting activity.")
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
                raise TemboardUIError(408, "Plugin not activated.")
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

            # Load activity.
            activity_data = temboard_activity(self.ssl_ca_cert_file,
                                              instance.agent_address,
                                              instance.agent_port, xsession)
            self.logger.info("Done.")
            return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='activity.html',
                data={
                    'nav': True,
                    'role': role,
                    'instance': instance,
                    'plugin': 'activity',
                    'activities': activity_data,
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
        run_background(self.get_activity, self.async_callback, (agent_address,
                                                                agent_port))


class ActivityWBHandler(BaseHandler):
    def get_activity_w_b(self, agent_address, agent_port, mode):
        try:
            self.logger.info("Getting waiting/blocking sessions.")
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
                raise TemboardUIError(408, "Plugin not activated.")
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

            # Load activity.
            if mode == 'waiting':
                activity_data = temboard_activity_waiting(
                    self.ssl_ca_cert_file, instance.agent_address,
                    instance.agent_port, xsession)
            elif mode == 'blocking':
                activity_data = temboard_activity_blocking(
                    self.ssl_ca_cert_file, instance.agent_address,
                    instance.agent_port, xsession)
            else:
                raise TemboardUIError(404, "Mode unknown.")
            self.logger.info("Done.")
            return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='activity_w_b.html',
                data={
                    'nav': True,
                    'role': role,
                    'instance': instance,
                    'plugin': 'activity',
                    'activities': activity_data,
                    'mode': mode,
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
    def get(self, agent_address, agent_port, mode):
        run_background(self.get_activity_w_b, self.async_callback,
                       (agent_address, agent_port, mode))


class ActivityProxyHandler(JsonHandler):
    def get_activity(self, agent_address, agent_port):
        try:
            self.logger.info("Getting activity (proxy).")
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
                raise TemboardUIError(408, "Plugin not activated.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise TemboardUIError(401, 'X-Session header missing')

            data_activity = temboard_activity(self.ssl_ca_cert_file,
                                              instance.agent_address,
                                              instance.agent_port, xsession)
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=data_activity)
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
        run_background(self.get_activity, self.async_callback, (agent_address,
                                                                agent_port))


class ActivityWBProxyHandler(JsonHandler):
    def get_activity_w_b(self, agent_address, agent_port, mode):
        try:
            self.logger.info("Getting waiting/blocking sessions (proxy).")
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
                raise TemboardUIError(408, "Plugin not activated.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise TemboardUIError(401, 'X-Session header missing')

            # Load activity.
            if mode == 'waiting':
                data_activity = temboard_activity_waiting(
                    self.ssl_ca_cert_file, instance.agent_address,
                    instance.agent_port, xsession)
            elif mode == 'blocking':
                data_activity = temboard_activity_blocking(
                    self.ssl_ca_cert_file, instance.agent_address,
                    instance.agent_port, xsession)
            else:
                raise TemboardUIError(404, "Mode unknown.")
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=data_activity)
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
    def get(self, agent_address, agent_port, mode):
        run_background(self.get_activity_w_b, self.async_callback,
                       (agent_address, agent_port, mode))


class ActivityKillProxyHandler(JsonHandler):
    def post_kill(self, agent_address, agent_port):
        try:
            self.logger.info("Posting terminate backend.")
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
                raise TemboardUIError(408, "Plugin not activated.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise TemboardUIError(401, 'X-Session header missing')

            self.logger.debug(tornado.escape.json_decode(self.request.body))
            data_kill = temboard_activity_kill(
                self.ssl_ca_cert_file, instance.agent_address,
                instance.agent_port, xsession,
                tornado.escape.json_decode(self.request.body))
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=data_kill)
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
    def post(self, agent_address, agent_port):
        run_background(self.post_kill, self.async_callback, (agent_address,
                                                             agent_port))
