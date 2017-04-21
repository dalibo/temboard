import tornado.web

from temboardui.errors import TemboardUIError
from temboardui.temboardclient import (
    TemboardError,
    temboard_get_notifications,
    temboard_profile,
)
from temboardui.handlers.base import BaseHandler
from temboardui.async import (
    HTMLAsyncResult,
    run_background,
)
from temboardui.application import get_instance


class NotificationsHandler(BaseHandler):
    def get_notifications(self, agent_address, agent_port):
        try:
            self.logger.info("Getting notifications.")
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

            # Load notifications.
            notifications = temboard_get_notifications(self.ssl_ca_cert_file,
                                                       instance.agent_address,
                                                       instance.agent_port,
                                                       xsession)
            self.logger.info("Done.")
            return HTMLAsyncResult(
                    http_code=200,
                    template_file='notifications.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'plugin': 'notifications',
                        'notifications': notifications,
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
                    return HTMLAsyncResult(http_code=401,
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
        run_background(self.get_notifications, self.async_callback,
                       (agent_address, agent_port))
