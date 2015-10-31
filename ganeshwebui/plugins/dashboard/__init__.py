import os
import tornado.web
from tornado.template import Loader
from ganeshwebui.handlers.base import JsonHandler, BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *
from ganeshwebui.async import *

def configuration(config):
    return {}

def get_routes(config):
    plugin_path = os.path.dirname(os.path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.ganesh['ssl_ca_cert_file'],
        'template_path':  plugin_path + "/templates"
    }
    routes = [
        (r"/server/(.*)/([0-9]{1,5})/dashboard", DashboardHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/dashboard", DashboardProxyHandler, handler_conf),
        (r"/js/dashboard/(.*)", tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
    ]
    return routes

class DashboardHandler(BaseHandler):

    def get_dashboard(self, ganeshd_host, ganeshd_port):
        dashboard_info = None
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
        try:
            dashboard_data = ganeshd_dashboard(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            dashboard_info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            return HTMLAsyncResult(
                http_code = 200,
                template_file = 'dashboard.html',
                template_path = self.template_path,
                data = {
                    'info': dashboard_info,
                    'ganeshd_host' : ganeshd['host'],
                    'ganeshd_port' : ganeshd['port'],
                    'dashboard' : dashboard_data,
                    'buffers_delta' : 0,
                    'readratio': (100 - dashboard_data['hitratio']),
                    'xsession': xsession,
                    'servers': GANESHD_SERVERS,
                    'current_page': 'dashboard'
                })
        except GaneshdError as e:
            if e.code == 401:
                return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            else:
                return HTMLAsyncResult(
                    http_code = e.code,
                    template_file = 'error.html',
                    data = {
                        'code': str(e.code),
                        'message': str(e.message),
                        'info': dashboard_info,
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'xsession': xsession,
                        'servers': GANESHD_SERVERS,
                        'current_page': 'dashboard'
                    })

    @tornado.web.asynchronous
    def get(self, ganeshd_host, ganeshd_port):
        run_background(self.get_dashboard, self.async_callback, (ganeshd_host, ganeshd_port))

class DashboardProxyHandler(JsonHandler):

    def get_dashboard(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            return JSONAsyncResult(http_code = 401, data = {'error': 'X-Session header missing'})
        try:
            dashboard_data = ganeshd_dashboard(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            return JSONAsyncResult(http_code = 200, data = dashboard_data)
        except GaneshdError as e:
            return JSONAsyncResult(http_code = e.code, data = {'error': e.message})

    @tornado.web.asynchronous
    def get(self, ganeshd_host, ganeshd_port):
        run_background(self.get_dashboard, self.async_callback, (ganeshd_host, ganeshd_port))
