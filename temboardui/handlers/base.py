import tornado.web
import json
from sqlalchemy.orm import sessionmaker, scoped_session

from temboardui.errors import TemboardUIError
from tornado.template import Loader
from temboardui.async import (
    CSVAsyncResult,
    HTMLAsyncResult,
    JSONAsyncResult,
)
from temboardui.model.tables import MetaData
from temboardui.model.orm import Roles
from temboardui.application import get_role_by_cookie


class BaseHandler(tornado.web.RequestHandler):

    def initialize(self, ssl_ca_cert_file, template_path):
        self.template_path = template_path
        self.ssl_ca_cert_file = ssl_ca_cert_file
        self.auth_cookie = None
        self.db_session = None

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
                                   expires_days=0.5)
        if async_result.http_code in (301, 302, 401) and \
           async_result.redirection is not None:
            self.set_secure_cookie('referer_uri', self.request.uri,
                                   expires_days=0.5)
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
                                   expires_days=0.5)
        if async_result.http_code == 200:
            self.write(json.dumps(async_result.data))
        else:
            self.set_status(async_result.http_code)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({'error': async_result.data['error']}))
        self.finish()


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
