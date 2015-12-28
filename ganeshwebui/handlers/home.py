import tornado.web

from ganeshwebui.handlers.base import BaseHandler
from ganeshwebui.async import *
from ganeshwebui.errors import GaneshError
from ganeshwebui.application import get_instances_by_role_name

class HomeHandler(BaseHandler):

    @tornado.web.asynchronous
    def get(self):
        run_background(self.get_home, self.async_callback)

    def get_home(self):
        try:
            self.load_auth_cookie()
            self.start_db_session()
            role = self.current_user
            if not role:
                raise GaneshError(302, 'Current role unknown.')
            instance_list = get_instances_by_role_name(self.db_session, role.role_name)
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()
            return HTMLAsyncResult(
                    http_code = 200,
                    template_file = 'home.html',
                    data = { 
                        'nav': True,
                        'role': role,
                        'instance_list': instance_list
                    })
        except (GaneshError, Exception) as e:
            self.logger.error(e.message)
            try:
                self.db_session.expunge_all()
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if isinstance(e, GaneshError):
                if e.code == 302:
                    return HTMLAsyncResult(302, '/login')
                elif e.code == 401:
                    return HTMLAsyncResult(
                            401,
                            None,
                            {'nav': False},
                            template_file = 'unauthorized.html')
            return HTMLAsyncResult(
                        500,
                        None,
                        {'nav': False, 'error': e.message},
                        template_file = 'error.html')
