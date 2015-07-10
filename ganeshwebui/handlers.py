import tornado.ioloop
import tornado.web
import tornado.escape
import urllib

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
            info = ganeshd_dashboard_info(ganeshd['host'], ganeshd['port'], xsession)
            self.render("dashboard.html",
                info = info,
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                dashboard = data,
                buffers_delta = 0,
                readratio = (100 - data['hitratio']),
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
        print(kwargs['exc_info'][1])
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

class AdministrationControlProxyHandler(JsonHandler):
    def post(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        # xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            raise tornado.web.HTTPError(401, reason = 'X-Session header missing')
        try:
            data = ganeshd_post_administration_control(ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            self.write(data)
        except GaneshdError as e:
            raise tornado.web.HTTPError(e.code, reason = e.message)

class LoginHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        info = None
        if xsession:
            try:
                info = ganeshd_dashboard_info(ganeshd['host'], ganeshd['port'], xsession)
            except GaneshdError as e:
                pass
        self.render("login.html",
            ganeshd_host = ganeshd['host'],
            ganeshd_port = ganeshd['port'],
            servers = GANESHD_SERVERS,
            xsession = xsession,
            info = info,
            current_page = 'login')

    def post(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        try:
            xsession = ganeshd_login(ganeshd['host'], ganeshd['port'], self.get_argument("username"), self.get_argument("password"))
            self.set_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']), xsession)
            self.redirect("dashboard")
        except GaneshdError as e:
            xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
            info = None
            if xsession:
                try:
                    info = ganeshd_dashboard_info(ganeshd['host'], ganeshd['port'], xsession)
                except GaneshdError as e:
                    pass
            self.render("login.html",
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                error = e.message,
                servers = GANESHD_SERVERS,
                xsession = xsession,
                info = info,
                current_page = 'login')

class AdministrationHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port, category = None):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        try:
            info = ganeshd_dashboard_info(ganeshd['host'], ganeshd['port'], xsession)
            configuration_status = ganeshd_get_configuration_status(ganeshd['host'], ganeshd['port'], xsession)
            configuration_cat = ganeshd_get_configuration_categories(ganeshd['host'], ganeshd['port'], xsession)
            if category == None:
                category = tornado.escape.url_escape(configuration_cat['categories'][0]) 
            data = ganeshd_get_configuration(ganeshd['host'], ganeshd['port'], xsession, tornado.escape.url_escape(tornado.escape.url_unescape(category)))
            self.render("configuration.html",
                info = info,
                data = data,
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                xsession = xsession,
                servers = GANESHD_SERVERS,
                current_page = 'administration/configuration',
                current_cat = tornado.escape.url_escape(tornado.escape.url_unescape(category)), 
                configuration_categories = configuration_cat,
                configuration_status = configuration_status
                )
        except GaneshdError as e:
            if e.code == 401:
                self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            else:
                self.render("error.html", code=str(e.code), message=str(e.message))

    def post(self, ganeshd_host, ganeshd_port, category = None):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        try:
            error_code = None
            error_message = None
            post_settings = self.request.arguments
            ret_post = None
            settings = {'settings': []}
            for setting_name, setting_value in post_settings.iteritems():
                settings['settings'].append({'name': setting_name, 'setting': setting_value[0]})
            try:
                ret_post = ganeshd_post_configuration(ganeshd['host'], ganeshd['port'], xsession, settings)
            except GaneshdError as e:
                error_code = e.code
                error_message = e.message    
            configuration_status = ganeshd_get_configuration_status(ganeshd['host'], ganeshd['port'], xsession)
            configuration_cat = ganeshd_get_configuration_categories(ganeshd['host'], ganeshd['port'], xsession)
            info = ganeshd_dashboard_info(ganeshd['host'], ganeshd['port'], xsession)
            if category == None:
                category = tornado.escape.url_escape(configuration_cat['categories'][0]) 
            data = ganeshd_get_configuration(ganeshd['host'], ganeshd['port'], xsession, tornado.escape.url_escape(tornado.escape.url_unescape(category)))
            self.render("configuration.html",
                info = info,
                data = data,
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                xsession = xsession,
                servers = GANESHD_SERVERS,
                current_page = 'administration/configuration',
                current_cat = tornado.escape.url_escape(tornado.escape.url_unescape(category)), 
                configuration_categories = configuration_cat,
                configuration_status = configuration_status,
                error_code = error_code,
                error_message = error_message,
                ret_post = ret_post
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
