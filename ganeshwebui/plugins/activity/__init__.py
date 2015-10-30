import os
import tornado.web

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
        (r"/server/(.*)/([0-9]{1,5})/activity", ActivityHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity", ActivityProxyHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/kill", ActivityKillProxyHandler, handler_conf),
        (r"/js/activity/(.*)", tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
    ]
    return routes

class ActivityHandler(BaseHandler):
    def get_activity(self, ganeshd_host, ganeshd_port):
        dashboard_info = None
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
        try:
            # Load activity.
            activity_data = ganeshd_activity(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            # Load host informations.
            dashboard_info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'activity.html',
                    data = {
                        'info': dashboard_info,
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'activities': activity_data,
                        'xsession': xsession,
                        'servers': GANESHD_SERVERS,
                        'current_page': 'activity'
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
        run_background(self.get_activity, self.async_callback, (ganeshd_host, ganeshd_port))


class ActivityProxyHandler(JsonHandler):
    def get_activity(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            return JSONAsyncResult(http_code = 401, data = {'error': 'X-Session header missing'})
        try:
            data_activity = ganeshd_activity(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            return JSONAsyncResult(http_code = 200, data = data_activity)
        except GaneshdError as e:
            return JSONAsyncResult(http_code = e.code, data = {'error': e.message})

    @tornado.web.asynchronous
    def get(self, ganeshd_host, ganeshd_port):
        run_background(self.get_activity, self.async_callback, (ganeshd_host, ganeshd_port))

class ActivityKillProxyHandler(JsonHandler):
    def post_kill(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            return JSONAsyncResult(http_code = 401, data = {'error': 'X-Session header missing'})
        try:
            data_kill = ganeshd_activity_kill(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            return JSONAsyncResult(http_code = 200, data = data_kill)
        except GaneshdError as e:
            return JSONAsyncResult(http_code = e.code, data = {'error': e.message})

    @tornado.web.asynchronous
    def post(self, ganeshd_host, ganeshd_port):
        run_background(self.post_kill, self.async_callback, (ganeshd_host, ganeshd_port))
