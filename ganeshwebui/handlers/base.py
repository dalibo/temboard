import tornado.web
import json

from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *
from tornado.template import Loader
from ganeshwebui.async import *

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, ssl_ca_cert_file, template_path):
        self.template_path = template_path
        self.ssl_ca_cert_file = ssl_ca_cert_file
    
    def get(self):
        self.redirect('/server/'+GANESHD_SERVERS[0]['host']+'/'+str(GANESHD_SERVERS[0]['port'])+'/dashboard')

    def async_callback(self, async_result):
        """
        Callback executed once the function called by run_background() returns
         something, async_result parameter must be a HTMLAsyncResult instance.
        This callback is in charge to render the final content (HTML) returned to the client.
        """
        if not isinstance(async_result, HTMLAsyncResult):
            self.finish()
            return
        if async_result.http_code in (302, 401) and async_result.redirection is not None:
            self.redirect(async_result.redirection)
        if async_result.http_code == 200:
            if async_result.template_path is not None:
                self.loader = Loader(async_result.template_path)
                self.write(self.loader.load(async_result.template_file).generate(**async_result.data))
                self.finish()
            else:
                self.render(async_result.template_file, **async_result.data)
        else:
            self.render(async_result.template_file, **async_result.data)

class JsonHandler(BaseHandler):
    """Request handler where requests and responses speak JSON."""
    def prepare(self):
        # Incorporate request JSON into arguments dictionary.
        if self.request.body:
            try:
                json_data = json.loads(self.request.body)
                self.request.arguments.update(json_data)
            except ValueError:
                message = 'Unable to parse JSON.'
                self.send_error(400, message=message) # Bad Request
 
        # Set up response dictionary.
        self.response = dict()
 
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
 
    def write_error(self, status_code, **kwargs):
        message = kwargs['exc_info'][1].reason
        self.response = {'error': message}
        self.write_json()
 
    def write_json(self):
        output = json.dumps(self.response)
        self.write(output)

    def async_callback(self, async_result):
        if not isinstance(async_result, JSONAsyncResult):
            self.finish()
            return
        if async_result.http_code == 200:
            self.write(json.dumps(async_result.data))
        else:
            self.set_status(async_result.http_code)
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({'error': async_result.data['error']}))
        self.finish()
