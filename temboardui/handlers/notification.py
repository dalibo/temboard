import tornado.web

from temboardui.errors import TemboardUIError
from temboardui.temboardclient import (
    temboard_get_notifications,
    temboard_profile,
)
from temboardui.handlers.base import BaseHandler
from temboardui.async import (
    HTMLAsyncResult,
    run_background,
)


class NotificationsHandler(BaseHandler):

    @BaseHandler.catch_errors
    def get_notifications(self, agent_address, agent_port):
        self.logger.info("Getting notifications.")

        self.setUp(agent_address, agent_port)

        xsession = self.get_secure_cookie(
            "temboard_%s_%s" % (agent_address, agent_port))
        if not xsession:
            raise TemboardUIError(401, "Authentication cookie is missing.")
        else:
            data_profile = temboard_profile(self.ssl_ca_cert_file,
                                            agent_address,
                                            agent_port,
                                            xsession)
            agent_username = data_profile['username']

        # Load notifications.
        notifications = temboard_get_notifications(self.ssl_ca_cert_file,
                                                   agent_address,
                                                   agent_port,
                                                   xsession)
        self.tearDown(commit=False)
        self.logger.info("Done.")
        return HTMLAsyncResult(
                http_code=200,
                template_file='notifications.html',
                data={
                    'nav': True,
                    'role': self.current_user,
                    'instance': self.instance,
                    'plugin': 'notifications',
                    'notifications': notifications,
                    'xsession': xsession,
                    'agent_username': agent_username,
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_notifications, self.async_callback,
                       (agent_address, agent_port))
