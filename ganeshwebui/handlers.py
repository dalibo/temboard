import tornado.ioloop
import tornado.web

from ganeshwebui.ganeshdclient import *

GANESHD_SERVERS = [
    {
        'hostname': 'test',
        'host': '127.0.0.2',
        'port': 2346
    },
    {
        'hostname': 'poseidon',
        'host': '127.0.0.1',
        'port': 2345
    }
]

def get_ganeshd_server(p_ganeshd_host, p_ganeshd_port):
    for server in GANESHD_SERVERS:
        if server['host'] == p_ganeshd_host and server['port'] == int(p_ganeshd_port):
            return server
    raise tornado.web.HTTPError(404)

class BaseHandler(tornado.web.RequestHandler):
    
    def write_error(self, status_code, **kwargs):
        self.write('Error %s' % status_code)

    def get(self):
        self.redirect('/server/'+GANESHD_SERVERS[0]['host']+'/'+str(GANESHD_SERVERS[0]['port'])+'/dashboard')

class DashboardHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        try:
            data = ganeshd_dashboard(ganeshd['host'], ganeshd['port'], xsession)
            self.render("dashboard.html",
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                hostname = data['hostname'],
                os_version = data['os_version'],
                size = data['databases']['total_size'],
                nb_db = data['databases']['databases'],
                time = data['databases']['time'],
                memory = data['memory'],
                cpu = data['cpu'],
                loadaverage = data['loadaverage'],
                buffers = data['buffers'],
                buffers_delta = 0,
                backends = data['active_backends']['nb'],
                hitratio = data['hitratio'],
                readratio = (100 - data['hitratio']),
                pg_version = data['pg_version'],
                n_cpu = data['n_cpu'],
                xsession = xsession,
                servers = GANESHD_SERVERS,
                current_page = 'dashboard' 
                )
        except GaneshdError as e:
            if e.code == 401:
                self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            else:
                self.render("error.html", code=str(e.code), message=str(e.message))

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

class DashboardProxyHandler(JsonHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        # xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            raise tornado.web.HTTPError(401, reason = 'X-Session header missing')
        try:
            data = ganeshd_dashboard(ganeshd['host'], ganeshd['port'], xsession)
            self.write(data)
        except GaneshdError as e:
            raise tornado.web.HTTPError(e.code, reason = e.message)

class LoginHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        self.render("login.html",
            ganeshd_host = ganeshd['host'],
            ganeshd_port = ganeshd['port'],
            servers = GANESHD_SERVERS,
            current_page = 'login')

    def post(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        try:
            xsession = ganeshd_login(ganeshd['host'], ganeshd['port'], self.get_argument("username"), self.get_argument("password"))
            self.set_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']), xsession)
            self.redirect("dashboard")
        except GaneshdError as e:
            self.render("login.html",
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                error = e.message,
                servers = GANESHD_SERVERS,
                current_page = 'login')
