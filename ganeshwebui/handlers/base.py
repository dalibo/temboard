import tornado.web
import json

from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, ssl_ca_cert_file):
        self.ssl_ca_cert_file = ssl_ca_cert_file
    
    def write_error(self, status_code, **kwargs):
        self.write('Error %s' % status_code)

    def get(self):
        self.redirect('/server/'+GANESHD_SERVERS[0]['host']+'/'+str(GANESHD_SERVERS[0]['port'])+'/dashboard')


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
