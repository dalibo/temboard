from ganeshwebui.handlers.base import BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *

class LoginHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        info = None
        if xsession:
            try:
                info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
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
            xsession = ganeshd_login(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], self.get_argument("username"), self.get_argument("password"))
            self.set_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']), xsession)
            self.redirect("dashboard")
        except GaneshdError as e:
            xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
            info = None
            if xsession:
                try:
                    info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
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
