import tornado.web
import json
from sqlalchemy.orm import sessionmaker, scoped_session
from functools import wraps

from temboardui.errors import TemboardUIError
from tornado.template import Loader
from temboardui.async import (
    CSVAsyncResult,
    HTMLAsyncResult,
    JSONAsyncResult,
)
from temboardui.temboardclient import TemboardError
from temboardui.model.tables import MetaData
from temboardui.model.orm import Roles
from temboardui.application import get_role_by_cookie, get_instance


class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, ssl_ca_cert_file, template_path):
        self.template_path = template_path
        self.ssl_ca_cert_file = ssl_ca_cert_file
        self.auth_cookie = None
        self.db_session = None
        self.instance = None

    def on_finish(self):
        self.tearDown()

    @property
    def logger(self,):
        return self.application.logger

    def get(self):
        self.redirect('/home')

    def get_current_user(self,):
        if self.auth_cookie and self.db_session:
            try:
                return get_role_by_cookie(self.db_session, self.auth_cookie)
            except Exception as e:
                self.logger.exception(e.message)
        return

    def check_admin(self,):
        if isinstance(self.current_user, Roles) and \
           self.current_user.is_admin is True:
            return
        raise TemboardUIError(401, "Unauthorized access.")

    def load_auth_cookie(self,):
        """
        Try to load secure cookie content.
        """
        cookie_content = self.get_secure_cookie('temboard')
        if cookie_content is None:
            raise TemboardUIError(302, "Authentication cookie is missing.")
        self.auth_cookie = cookie_content

    def start_db_session(self):
        """
        Try to start a new DB session (local to current thread).
        """
        MetaData.bind = self.application.engine
        try:
            session_factory = sessionmaker(bind=self.application.engine)
            Session = scoped_session(session_factory)
            self.db_session = Session()
        except Exception as e:
            self.logger.exception(e.message)
            raise TemboardUIError(500,
                                  "Unable to create a new database session.")

    def async_callback(self, async_result):
        """
        Callback executed once the function called by run_background() returns
        something, async_result single arg must be an HTMLAsyncResult instance.
        This callback is in charge to render the final HTML content returned to
        the client.
        """
        if not isinstance(async_result, HTMLAsyncResult):
            self.finish()
            return
        if async_result.secure_cookie is not None and \
           'name' in async_result.secure_cookie and \
           'content' in async_result.secure_cookie:
            self.set_secure_cookie(async_result.secure_cookie['name'],
                                   async_result.secure_cookie['content'],
                                   expires_days=30)
        if async_result.http_code in (301, 302, 401) and \
           async_result.redirection is not None:
            self.set_secure_cookie('referer_uri', self.request.uri,
                                   expires_days=30)
            self.redirect(async_result.redirection)
            return
        if async_result.http_code == 200:
            if async_result.template_path is not None:
                self.loader = Loader(async_result.template_path)
                self.write(self.loader.load(async_result.template_file)
                           .generate(**async_result.data))
                self.finish()
                return
            else:
                self.render(async_result.template_file, **async_result.data)
                return
        else:
            self.render(async_result.template_file, **async_result.data)
            return

    def require_instance(self):
        if not self.instance:
            raise TemboardUIError(404, "Instance not found.")

    def check_active_plugin(self, name):
        '''
        Ensure that the plugin is active for given instance
        '''
        if name not in [p.plugin_name for p in self.instance.plugins]:
            raise TemboardUIError(408, "Plugin not activated.")

    @staticmethod
    def catch_errors(func):
        '''
        Decorator to catch and handle exceptions
        '''
        @wraps(func)
        def func_wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)

            except (TemboardUIError, TemboardError, Exception) as e:
                self.logger.exception(str(e))
                self.logger.info("Failed.")
                return self.handle_exceptions(e)
        return func_wrapper

    def handle_exceptions(self, e):
        '''
        Generic method to handle exceptions.
        May be overriden by inherited classes.
        '''
        try:
            if (isinstance(e, TemboardUIError) or
               isinstance(e, TemboardError)):
                if e.code == 401:
                    return HTMLAsyncResult(
                        http_code=401,
                        redirection="/server/%s/%s/login" %
                                    (self.instance.agent_address,
                                     self.instance.agent_port))
                elif e.code == 302:
                    return HTMLAsyncResult(http_code=401,
                                           redirection="/login")
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                        http_code=code,
                        template_file='error.html',
                        data={
                            'nav': True,
                            'role': self.role,
                            'instance': self.instance,
                            'code': e.code,
                            'error': e.message
                        })
        except Exception as e:
            self.logger.error(str(e))

    def setUp(self, address=None, port=None):
        '''
        Start DB Session.
        Get instance and ensure that it exists.
        Authenticate user.
        '''
        self.start_db_session()
        self.load_auth_cookie()
        if not self.current_user:
            raise TemboardUIError(302, "Current role unknown.")
        self.role = self.current_user
        if address is not None and port is not None:
            self.instance = get_instance(self.db_session, address, port)
            self.require_instance()

    def tearDown(self, commit=True):
        try:
            if commit:
                self.db_session.commit()
            self.db_session.close()
        except Exception:
            pass


class Error404Handler(tornado.web.RequestHandler):
    def prepare(self,):
        raise tornado.web.HTTPError(404)

    def write_error(self, status_code, **kwargs):
        if "Content-Type" in self.request.headers and \
           self.request.headers["Content-Type"].startswith("application/json"):
            self.set_header('Content-Type', 'application/json')
            output = json.dumps({'error': 'Not found.'})
            self.write(output)
        else:
            self.write('404: Not found.')


class JsonHandler(BaseHandler):
    """Request handler where requests and responses speak JSON."""
    def prepare(self):
        # Incorporate request JSON into arguments dictionary.
        if self.request.body:
            try:
                json_data = json.loads(self.request.body)
                self.request.arguments.update(json_data)
            except Exception as e:
                self.logger.exception(e.message)
                message = 'Unable to parse JSON.'
                self.send_error(400, error=message)

        # Set up response dictionary.
        self.response = dict()

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, **kwargs):
        try:
            self.response = {'error': kwargs['exc_info'][1].reason}
            self.write_json()
        except (KeyError, AttributeError):
            self.write(kwargs)

    def write_json(self):
        output = json.dumps(self.response)
        self.write(output)

    def async_callback(self, async_result):
        if not isinstance(async_result, JSONAsyncResult):
            self.finish()
            return
        if hasattr(async_result, 'secure_cookie') and \
           async_result.secure_cookie is not None and \
           'name' in async_result.secure_cookie and \
           'content' in async_result.secure_cookie:
            self.set_secure_cookie(async_result.secure_cookie['name'],
                                   async_result.secure_cookie['content'],
                                   expires_days=30)
        if async_result.http_code == 200:
            self.write(json.dumps(async_result.data))
        else:
            self.set_status(async_result.http_code)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({'error': async_result.data['error']}))
        self.finish()

    def handle_exceptions(self, e):
        try:
            self.db_session.rollback()
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


class CsvHandler(BaseHandler):
    def async_callback(self, async_result):
        self.set_header('Content-Type', async_result.content_type)
        if not isinstance(async_result, CSVAsyncResult):
            self.finish()
            return
        if async_result.http_code == 200:
            self.write(async_result.data)
        else:
            self.set_status(async_result.http_code)
            self.write(async_result.data['error'])
        self.finish()

    def handle_exceptions(self, e):
        try:
            self.db_session.rollback()
            self.db_session.close()
        except Exception:
            pass
        if int(self.get_argument('noerror', default=0)) == 1:
            return CSVAsyncResult(http_code=200, data=u'')
        else:
            if (isinstance(e, TemboardUIError)):
                return CSVAsyncResult(http_code=e.code,
                                      data={'error': e.message})
            else:
                return CSVAsyncResult(http_code=500,
                                      data={'error': e.message})
