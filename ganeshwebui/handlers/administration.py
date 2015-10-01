from tornado.web import HTTPError
import tornado.escape

from ganeshwebui.handlers.base import JsonHandler, BaseHandler
from ganeshwebui.tools import *
from ganeshwebui.ganeshdclient import *

class AdminControlProxyHandler(JsonHandler):
    def post(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise HTTPError(401, reason = 'X-Session header missing')
        try:
            data = ganeshd_post_administration_control(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            self.write(data)
        except GaneshdError as e:
            raise HTTPError(e.code, reason = e.message)

class AdminConfigurationProxyHandler(JsonHandler):
    def post(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            raise HTTPError(401, reason = 'X-Session header missing')
        try:
            data = ganeshd_post_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            self.write(data)
        except GaneshdError as e:
            raise HTTPError(e.code, reason = e.message)

class AdminConfigurationHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port, category = None):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        info = None
        try:
            info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            configuration_status = ganeshd_get_configuration_status(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            configuration_cat = ganeshd_get_configuration_categories(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            query_filter = self.get_argument('filter', None, True)
            if category == None:
                category = tornado.escape.url_escape(configuration_cat['categories'][0]) 
            data = ganeshd_get_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.url_escape(tornado.escape.url_unescape(category)), query_filter)
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
                query_filter = query_filter
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
                    current_page = 'administration/configuration',
                )

    def post(self, ganeshd_host, ganeshd_port, category = None):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        query_filter = self.get_argument('filter', None, True)
        info = None
        try:
            error_code = None
            error_message = None
            post_settings = self.request.arguments
            ret_post = None
            settings = {'settings': []}
            for setting_name, setting_value in post_settings.iteritems():
                if setting_name == 'filter':
                    continue
                settings['settings'].append({'name': setting_name, 'setting': setting_value[0]})
            try:
                ret_post = ganeshd_post_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, settings)
            except GaneshdError as e:
                error_code = e.code
                error_message = e.message    
            configuration_status = ganeshd_get_configuration_status(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            configuration_cat = ganeshd_get_configuration_categories(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            if category == None:
                category = tornado.escape.url_escape(configuration_cat['categories'][0]) 
            data = ganeshd_get_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.url_escape(tornado.escape.url_unescape(category)), query_filter)
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
                ret_post = ret_post,
                query_filter = query_filter
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
                    current_page = 'administration/configuration',
                )

class AdminConfigurationFileHandler(BaseHandler):
    def get(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        info = None
        try:
            info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            file_content = ganeshd_get_file_content(self.ssl_ca_cert_file, self.file_type, ganeshd['host'], ganeshd['port'], xsession)
            self.render("edit_file.html",
                file_type = self.file_type,
                info = info,
                file_content = file_content,
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                xsession = xsession,
                servers = GANESHD_SERVERS,
                current_page = 'administration/%s' % (self.file_type,)
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
                    current_page = 'administration/%s' % (self.file_type,),
                )

    def post(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))
        if not xsession:
            self.redirect("/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            return
        info = None
        error_code = None
        error_message = None
        ret_post = None
        try:
            try:
                ret_post = ganeshd_post_file_content(self.ssl_ca_cert_file, self.file_type, ganeshd['host'], ganeshd['port'], xsession, {'content': self.request.arguments['content']})
                ret_post = ganeshd_post_administration_control(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, {'action': 'reload'})
            except GaneshdError as e:
                error_code = e.code
                error_message = e.message    
            info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            file_content = ganeshd_get_file_content(self.ssl_ca_cert_file, self.file_type, ganeshd['host'], ganeshd['port'], xsession)
            self.render("edit_file.html",
                file_type = self.file_type,
                info = info,
                file_content = file_content,
                ganeshd_host = ganeshd['host'],
                ganeshd_port = ganeshd['port'],
                error_code = error_code,
                error_message = error_message,
                xsession = xsession,
                servers = GANESHD_SERVERS,
                current_page = 'administration/%s' % (self.file_type,),
                ret_post = ret_post
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
                    current_page = 'administration/%s' % (self.file_type,),
                )


class AdminHBAHandler(AdminConfigurationFileHandler):
    file_type = 'hba'

class AdminPGIdentHandler(AdminConfigurationFileHandler):
    file_type = 'pg_ident'
