from tornado.web import HTTPError

from ganeshwebui.handlers.base import JsonHandler, BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *

class ActivityHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        info = None
        try:
            data = ganeshd_activity(ganeshd['host'], ganeshd['port'], xsession)
            info = ganeshd_dashboard_info(ganeshd['host'], ganeshd['port'], xsession)
            self.render("activity.html",
                info = info,
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                activities = data,
                xsession = xsession,
                servers = GANESHD_SERVERS,
                current_page = 'activity'
                )
        except GaneshdError as e:
            if e.code == 401:
                self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            else:
                self.render("error.html",
                    code=str(e.code),
                    message=str(e.message),
                    info = info,
                    ganeshd_host = ganeshd['host'],
                    ganeshd_port = ganeshd['port'],
                    xsession = xsession,
                    servers = GANESHD_SERVERS,
                    current_page = 'dashboard',
                )

class ActivityProxyHandler(JsonHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise HTTPError(401, reason = 'X-Session header missing')
        try:
            data = ganeshd_activity(ganeshd['host'], ganeshd['port'], xsession)
            self.write(data)
        except GaneshdError as e:
            raise HTTPError(e.code, reason = e.message)

class ActivityKillProxyHandler(JsonHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise HTTPError(401, reason = 'X-Session header missing')
        try:
            data = ganeshd_activity_kill(ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            self.write(data)
        except GaneshdError as e:
            raise HTTPError(e.code, reason = e.message)
