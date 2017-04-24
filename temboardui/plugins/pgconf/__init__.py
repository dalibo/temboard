from os import path
import tornado.web
import tornado.escape

from temboardui.handlers.base import JsonHandler, BaseHandler
from temboardui.temboardclient import (
    TemboardError,
    temboard_delete_hba_version,
    temboard_get_conf_file,
    temboard_get_conf_file_raw,
    temboard_get_conf_file_versions,
    temboard_get_configuration,
    temboard_get_configuration_categories,
    temboard_get_configuration_status,
    temboard_get_file_content,
    temboard_get_hba_options,
    temboard_post_administration_control,
    temboard_post_conf_file,
    temboard_post_configuration,
    temboard_post_file_content,
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
            r"/server/(.*)/([0-9]{1,5})/pgconf/hba",
            HBAHandler,
            handler_conf
        ),
        (
            r"/server/(.*)/([0-9]{1,5})/pgconf/pg_ident",
            PGIdentHandler,
            handler_conf
        ),
        (
            r"/proxy/(.*)/([0-9]{1,5})/administration/control",
            AdminControlProxyHandler,
            handler_conf
        ),
        (
            r"/proxy/(.*)/([0-9]{1,5})/pgconf/configuration",
            ConfigurationProxyHandler,
            handler_conf
        ),
        (
            r"/proxy/(.*)/([0-9]{1,5})/pgconf/hba/options",
            HBAOptionsProxyHandler,
            handler_conf
        ),
        (
            r"/proxy/(.*)/([0-9]{1,5})/pgconf/hba$",
            HBAProxyHandler,
            handler_conf
        ),
        (
            r"/proxy/(.*)/([0-9]{1,5})/pgconf/hba/delete$",
            HBADeleteProxyHandler,
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

    def get_configuration(self, agent_address, agent_port, category=None):
        try:
            self.logger.info("Getting configuration.")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")
            else:
                data_profile = temboard_profile(self.ssl_ca_cert_file,
                                                instance.agent_address,
                                                instance.agent_port,
                                                xsession)
                agent_username = data_profile['username']

            configuration_status = temboard_get_configuration_status(
                                        self.ssl_ca_cert_file,
                                        instance.agent_address,
                                        instance.agent_port,
                                        xsession)
            configuration_cat = temboard_get_configuration_categories(
                                        self.ssl_ca_cert_file,
                                        instance.agent_address,
                                        instance.agent_port,
                                        xsession)
            query_filter = self.get_argument('filter', None, True)
            if category is None:
                category = tornado.escape.url_escape(
                    configuration_cat['categories'][0])
            url = tornado.escape.url_escape(
                tornado.escape.url_unescape(category))
            configuration_data = temboard_get_configuration(
                self.ssl_ca_cert_file,
                instance.agent_address,
                instance.agent_port,
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
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
                        'data': configuration_data,
                        'xsession': xsession,
                        'agent_username': agent_username,
                        'current_cat': tornado.escape.url_unescape(category),
                        'configuration_categories': configuration_cat,
                        'configuration_status': configuration_status,
                        'query_filter': query_filter
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
                        redirection="/server/%s/%s/login" %
                                    (agent_address, agent_port))
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
    def get(self, agent_address, agent_port, category=None):
        run_background(self.get_configuration, self.async_callback,
                       (agent_address, agent_port, category))

    def post_configuration(self, agent_address, agent_port, category=None):
        try:
            self.logger.info("Posting configuration.")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
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
                                instance.agent_address,
                                instance.agent_port,
                                xsession,
                                settings)
            except TemboardError as e:
                error_code = e.code
                error_message = e.message
            # Get PostgreSQL configuration status: needs restart, reload or is
            # fine.
            configuration_status = temboard_get_configuration_status(
                                        self.ssl_ca_cert_file,
                                        instance.agent_address,
                                        instance.agent_port,
                                        xsession)
            # Load settings categories.
            configuration_cat = temboard_get_configuration_categories(
                                    self.ssl_ca_cert_file,
                                    instance.agent_address,
                                    instance.agent_port,
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
                                    instance.agent_address,
                                    instance.agent_port,
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
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
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
                        redirection="/server/%s/%s/login" %
                                    (agent_address, agent_port))
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
    def post(self, agent_address, agent_port, category=None):
        run_background(self.post_configuration, self.async_callback,
                       (agent_address, agent_port, category))


class ConfigurationFileHandler(BaseHandler):
    def get_configuration_file(self, agent_address, agent_port):
        try:
            self.logger.info("Getting configuration (file).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")

            # Load file content.
            file_content = temboard_get_file_content(
                                self.ssl_ca_cert_file,
                                self.file_type,
                                instance.agent_address,
                                instance.agent_port,
                                xsession)
            self.logger.info("Done.")
            return HTMLAsyncResult(
                    http_code=200,
                    template_path=self.template_path,
                    template_file='edit_file.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
                        'file_type': self.file_type,
                        'file_content': file_content,
                        'xsession': xsession
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
                        redirection="/server/%s/%s/login" %
                                    (agent_address, agent_port))
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
        run_background(self.get_configuration_file, self.async_callback,
                       (agent_address, agent_port))

    def post_configuration_file(self, agent_address, agent_port):
        error_code = None
        error_message = None
        ret_post = None
        try:
            self.logger.info("Posting configuration (file).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")
            try:
                # Send file content ..
                ret_post = temboard_post_file_content(
                    self.ssl_ca_cert_file,
                    self.file_type,
                    instance.agent_address,
                    instance.agent_port,
                    xsession,
                    {
                        'content': self.request.arguments['content'][0],
                        'new_version': True
                    }
                )
                # .. and reload configuration.
                ret_post = temboard_post_administration_control(
                                self.ssl_ca_cert_file,
                                instance.agent_address,
                                instance.agent_port,
                                xsession,
                                {'action': 'reload'})
            except (TemboardError, Exception) as e:
                self.logger.exception(str(e))
                if isinstance(TemboardError, e):
                    error_code = e.code
                    error_message = e.message
                else:
                    error_code = 500
                    error_message = "Internale error."
            # Load file content.
            file_content = temboard_get_file_content(
                                self.ssl_ca_cert_file,
                                self.file_type,
                                instance.agent_address,
                                instance.agent_port,
                                xsession)
            self.logger.info("Done.")
            return HTMLAsyncResult(
                    http_code=200,
                    template_path=self.template_path,
                    template_file='edit_file.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
                        'file_type': self.file_type,
                        'file_content': file_content,
                        'error_code': error_code,
                        'error_message': error_message,
                        'xsession': xsession,
                        'ret_post': ret_post
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
                        redirection="/server/%s/%s/login" %
                                    (agent_address, agent_port))
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
    def post(self, agent_address, agent_port):
        run_background(self.post_configuration_file, self.async_callback,
                       (agent_address, agent_port))


class ConfigurationFileVersioningHandler(BaseHandler):
    def check_etag_header(_):
        """
        This is required because we don't want to return a 304 HTTP code when
        clients send etag header (like jquery does on .load() calls).
        """
        return False

    def get_configuration_file(self, agent_address, agent_port):
        try:
            self.logger.info("Getting configuration (file).")
            instance = None
            role = None
            self.load_auth_cookie()
            self.start_db_session()
            mode = self.get_argument('mode', None)
            version = self.get_argument('version', None)
            role = self.current_user

            if not role:
                raise TemboardUIError(302, "Current role unknown.")
            if mode is None and len(self.available_modes) > 0:
                mode = self.available_modes[0]
            if not (mode in self.available_modes):
                raise TemboardUIError(404, "Editing mode not available.")
            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")
            file_versions = temboard_get_conf_file_versions(
                        self.ssl_ca_cert_file,
                        self.file_type,
                        instance.agent_address,
                        instance.agent_port,
                        xsession)
            if mode == 'raw':
                # Load file content.
                conf_file_raw = temboard_get_conf_file_raw(
                                self.ssl_ca_cert_file,
                                self.file_type,
                                version,
                                instance.agent_address,
                                instance.agent_port,
                                xsession)
                self.logger.info("Done.")
                return HTMLAsyncResult(
                    http_code=200,
                    template_path=self.template_path,
                    template_file='edit_conf_file_raw.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
                        'file_versions': file_versions,
                        'file_type': self.file_type,
                        'conf_file_raw': conf_file_raw,
                        'xsession': xsession
                    })
            if mode == 'advanced':
                hba_options = None
                if self.file_type == 'hba':
                    hba_options = temboard_get_hba_options(
                                    self.ssl_ca_cert_file,
                                    instance.agent_address,
                                    instance.agent_port,
                                    xsession)
                conf_file = temboard_get_conf_file(
                                self.ssl_ca_cert_file,
                                self.file_type,
                                version,
                                instance.agent_address,
                                instance.agent_port,
                                xsession)
                self.logger.info("Done.")
                return HTMLAsyncResult(
                    http_code=200,
                    template_path=self.template_path,
                    template_file='edit_conf_file_advanced.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
                        'file_versions': file_versions,
                        'file_type': self.file_type,
                        'conf_file': conf_file,
                        'hba_options': hba_options,
                        'xsession': xsession
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
                        redirection="/server/%s/%s/login" %
                        (agent_address, agent_port))
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
        run_background(self.get_configuration_file, self.async_callback,
                       (agent_address, agent_port))

    def post_configuration_file(self, agent_address, agent_port):
        error_code = None
        error_message = None
        ret_post = None
        try:
            self.logger.info("Posting configuration (file).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")
            try:
                # Send file content ..
                ret_post = temboard_post_file_content(
                    self.ssl_ca_cert_file,
                    self.file_type,
                    instance.agent_address,
                    instance.agent_port,
                    xsession,
                    {
                        'content': self.request.arguments['content'][0],
                        'new_version': True
                    }
                )
                # .. and reload configuration.
                ret_post = temboard_post_administration_control(
                                self.ssl_ca_cert_file,
                                instance.agent_address,
                                instance.agent_port,
                                xsession,
                                {'action': 'reload'})
            except (TemboardError, Exception) as e:
                self.logger.exception(str(e))
                if isinstance(TemboardError, e):
                    error_code = e.code
                    error_message = e.message
                else:
                    error_code = 500
                    error_message = "Internale error."
            # Load file content.
            file_content = temboard_get_file_content(
                                self.ssl_ca_cert_file,
                                self.file_type,
                                instance.agent_address,
                                instance.agent_port,
                                xsession)
            self.logger.info("Done.")
            return HTMLAsyncResult(
                    http_code=200,
                    template_path=self.template_path,
                    template_file='edit_file.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'plugin': 'pgconf',
                        'file_type': self.file_type,
                        'file_content': file_content,
                        'error_code': error_code,
                        'error_message': error_message,
                        'xsession': xsession,
                        'ret_post': ret_post
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
                        redirection="/server/%s/%s/login" %
                                    (agent_address, agent_port))
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
    def post(self, agent_address, agent_port):
        run_background(self.post_configuration_file, self.async_callback,
                       (agent_address, agent_port))


class HBAHandler(ConfigurationFileVersioningHandler):
    file_type = 'hba'
    available_modes = ['advanced', 'raw']


class PGIdentHandler(ConfigurationFileHandler):
    file_type = 'pg_ident'


"""
Proxy Handlers
"""


class AdminControlProxyHandler(JsonHandler):
    """ /administration/control JSON handler """

    def post_control(self, agent_address, agent_port):
        try:
            self.logger.info("Posting control (proxy).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")

            data = temboard_post_administration_control(
                        self.ssl_ca_cert_file,
                        instance.agent_address,
                        instance.agent_port,
                        xsession,
                        tornado.escape.json_decode(self.request.body))
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=data)
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_control, self.async_callback,
                       (agent_address, agent_port))


class ConfigurationProxyHandler(JsonHandler):
    """ /pgconf/configuration JSON handler """

    def post_configuration(self, agent_address, agent_port):
        try:
            self.logger.info("Posting configuration (proxy).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
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
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_configuration, self.async_callback,
                       (agent_address, agent_port))


class HBAOptionsProxyHandler(JsonHandler):
    def get_hba_options(self, agent_address, agent_port):
        try:
            self.logger.info("Getting HBA options (proxy).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not activated.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.request.headers.get('X-Session')
            if not xsession:
                raise TemboardUIError(401, 'X-Session header missing')

            hba_options = temboard_get_hba_options(
                self.ssl_ca_cert_file, instance.agent_address,
                instance.agent_port, xsession)
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=hba_options)
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_hba_options, self.async_callback,
                       (agent_address, agent_port))


class HBAProxyHandler(JsonHandler):
    def post_hba(self, agent_address, agent_port):
        try:
            self.logger.info("Posting HBA (proxy).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")

            data = temboard_post_conf_file(
                        self.ssl_ca_cert_file,
                        'hba',
                        instance.agent_address,
                        instance.agent_port,
                        xsession,
                        tornado.escape.json_decode(self.request.body))
            # And reload postgresql configuration.
            temboard_post_administration_control(
                self.ssl_ca_cert_file,
                instance.agent_address,
                instance.agent_port,
                xsession,
                {'action': 'reload'})
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=data)
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def post(self, agent_address, agent_port):
        run_background(self.post_hba, self.async_callback,
                       (agent_address, agent_port))


class HBADeleteProxyHandler(JsonHandler):
    def delete_hba(self, agent_address, agent_port):
        try:
            self.logger.info("Deleting HBA (proxy).")
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
            if __name__ not in [plugin.plugin_name
                                for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))
            if not xsession:
                raise TemboardUIError(401, "Authentication cookie is missing.")

            res = temboard_delete_hba_version(
                        self.ssl_ca_cert_file,
                        instance.agent_address,
                        instance.agent_port,
                        xsession,
                        self.get_argument('version', None))
            self.logger.info("Done.")
            return JSONAsyncResult(http_code=200, data=res)
        except (TemboardUIError, TemboardError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                return JSONAsyncResult(http_code=e.code,
                                       data={'error': e.message})
            else:
                return JSONAsyncResult(http_code=500,
                                       data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.delete_hba, self.async_callback,
                       (agent_address, agent_port))
