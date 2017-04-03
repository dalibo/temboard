import tornado.web

from temboardui.handlers.base import BaseHandler
from temboardui.async import (
    HTMLAsyncResult,
    run_background,
)
from temboardui.errors import TemboardUIError
from temboardui.application import get_instances_by_role_name


class HomeHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        run_background(self.get_home, self.async_callback)

    def get_home(self):
        try:
            self.logger.info("Loading home.")
            self.load_auth_cookie()
            self.start_db_session()
            role = self.current_user
            if not role:
                raise TemboardUIError(302, 'Current role unknown.')
            instance_list = get_instances_by_role_name(self.db_session,
                                                       role.role_name)
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            self.logger.info("Done.")
            return HTMLAsyncResult(
                    http_code=200,
                    template_file='home.html',
                    data={
                        'nav': True,
                        'role': role,
                        'instance_list': instance_list
                    })
        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            self.logger.info("Failed.")
            try:
                self.db_session.expunge_all()
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, TemboardUIError):
                if e.code == 302:
                    return HTMLAsyncResult(302, '/login')
                elif e.code == 401:
                    return HTMLAsyncResult(
                            401,
                            None,
                            {'nav': False},
                            template_file='unauthorized.html')
            return HTMLAsyncResult(
                        500,
                        None,
                        {'nav': False, 'error': e.message},
                        template_file='error.html')
