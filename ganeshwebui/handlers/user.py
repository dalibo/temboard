import tornado.web
from ganeshwebui.handlers.base import BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *
from ganeshwebui.async import *

class LoginHandler(BaseHandler):
    """ Login Handler """

    def get_login(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        info = None
        if xsession:
            try:
                info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            except GaneshdError as e:
                pass
        return HTMLAsyncResult(
                http_code = 200,
                template_file = 'login.html',
                data = {
                    'ganeshd_host': ganeshd['host'],
                    'ganeshd_port': ganeshd['port'],
                    'servers': GANESHD_SERVERS,
                    'xsession': xsession,
                    'info': info,
                    'current_page': 'login'
                })

    @tornado.web.asynchronous
    def get(self, ganeshd_host, ganeshd_port):
        run_background(self.get_login, self.async_callback, (ganeshd_host, ganeshd_port))

    def post_login(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        try:
            xsession = ganeshd_login(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], self.get_argument("username"), self.get_argument("password"))
            self.set_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']), xsession)
            self.redirect("dashboard")
        except (GaneshdError, Exception) as e:
            xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
            info = None
            if xsession:
                try:
                    info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
                except GaneshdError as ge:
                    pass
            return HTMLAsyncResult(
                    http_code = 200,
                    template_file = 'login.html',
                    data = {
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'error': e.message,
                        'servers': GANESHD_SERVERS,
                        'xsession': xsession,
                        'info': info,
                        'current_page': 'login'
                    })

    @tornado.web.asynchronous
    def post(self, ganeshd_host, ganeshd_port):
        run_background(self.post_login, self.async_callback, (ganeshd_host, ganeshd_port))
