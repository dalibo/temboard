import os
import tornado.web
import tornado.escape

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
        (r"/server/(.*)/([0-9]{1,5})/administration/configuration$", AdminConfigurationHandler, handler_conf),
        (r"/server/(.*)/([0-9]{1,5})/administration/configuration/category/(.+)$", AdminConfigurationHandler, handler_conf),
        (r"/server/(.*)/([0-9]{1,5})/administration/hba", AdminHBAHandler, handler_conf),
        (r"/server/(.*)/([0-9]{1,5})/administration/pg_ident", AdminPGIdentHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/administration/control", AdminControlProxyHandler, handler_conf),
        (r"/proxy/(.*)/([0-9]{1,5})/administration/configuration", AdminConfigurationProxyHandler, handler_conf),
        (r"/js/administration/(.*)", tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
    ]
    return routes


class AdminControlProxyHandler(JsonHandler):
    """ /administration/control JSON handler """

    def post_control(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            return JSONAsyncResult(http_code = 401, data = { 'error': 'X-Session header missing'})
        try:
            data = ganeshd_post_administration_control(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            return JSONAsyncResult(http_code = 200, data = data)
        except GaneshdError as e:
            return JSONAsyncResult(http_code = e.code, data = {'error': e.message})

    @tornado.web.asynchronous
    def post(self, ganeshd_host, ganeshd_port):
        run_background(self.post_control, self.async_callback, (ganeshd_host, ganeshd_port))

class AdminConfigurationProxyHandler(JsonHandler):
    """ /administration/configuration JSON handler """

    def post_configuration(self, ganeshd_host, ganeshd_port):
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.request.headers.get('X-Session')
        if not xsession:
            return JSONAsyncResult(http_code = 401, data = { 'error': 'X-Session header missing'})
        try:
            data = ganeshd_post_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.json_decode(self.request.body))
            return JSONAsyncResult(http_code = 200, data = data)
        except GaneshdError as e:
            return JSONAsyncResult(http_code = e.code, data = {'error': e.message})

    @tornado.web.asynchronous
    def post(self, ganeshd_host, ganeshd_port):
        run_background(self.post_configuration, self.async_callback, (ganeshd_host, ganeshd_port))


class AdminConfigurationHandler(BaseHandler):
    """ Settings HTML handler """

    def get_configuration(self, ganeshd_host, ganeshd_port, category = None):
        dashboard_info = None
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))

        if not xsession:
            return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
        try:
            dashboard_info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            configuration_status = ganeshd_get_configuration_status(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            configuration_cat = ganeshd_get_configuration_categories(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            query_filter = self.get_argument('filter', None, True)
            if category == None:
                category = tornado.escape.url_escape(configuration_cat['categories'][0]) 
            configuration_data = ganeshd_get_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.url_escape(tornado.escape.url_unescape(category)), query_filter)
            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'configuration.html',
                    data = {
                        'info': dashboard_info,
                        'data': configuration_data,
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'xsession': xsession,
                        'servers': GANESHD_SERVERS,
                        'current_page': 'administration/configuration',
                        'current_cat': tornado.escape.url_escape(tornado.escape.url_unescape(category)), 
                        'configuration_categories': configuration_cat,
                        'configuration_status': configuration_status,
                        'query_filter': query_filter
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
                            'current_page': 'administration/configuration'
                        })

    @tornado.web.asynchronous
    def get(self, ganeshd_host, ganeshd_port, category = None):
        run_background(self.get_configuration, self.async_callback, (ganeshd_host, ganeshd_port, category))

    def post_configuration(self, ganeshd_host, ganeshd_port, category = None):
        dashboard_info = None
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))

        if not xsession:
            return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
        query_filter = self.get_argument('filter', None, True)
        try:
            error_code = None
            error_message = None
            post_settings = self.request.arguments
            ret_post = None
            settings = {'settings': []}
            for setting_name, setting_value in post_settings.iteritems():
                # 'filter' is not a setting, just ignore it.
                if setting_name == 'filter':
                    continue
                settings['settings'].append({'name': setting_name, 'setting': setting_value[0]})
            try:
                # Try to send the setting to ganeshd agent.
                ret_post = ganeshd_post_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, settings)
            except GaneshdError as e:
                error_code = e.code
                error_message = e.message
            # Get PostgreSQL configuration status: needs restart, reload or is fine.
            configuration_status = ganeshd_get_configuration_status(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            # Load settings categories.
            configuration_cat = ganeshd_get_configuration_categories(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            # Get host & PG instance informations.
            dashboard_info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            if category == None:
                category = tornado.escape.url_escape(configuration_cat['categories'][0]) 
            # Load settings depending on the current category or the filter value.
            configuration_data = ganeshd_get_configuration(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, tornado.escape.url_escape(tornado.escape.url_unescape(category)), query_filter)
            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'configuration.html',
                    data = {
                        'info': dashboard_info,
                        'data': configuration_data,
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'xsession': xsession,
                        'servers': GANESHD_SERVERS,
                        'current_page': 'administration/configuration',
                        'current_cat': tornado.escape.url_escape(tornado.escape.url_unescape(category)), 
                        'configuration_categories': configuration_cat,
                        'configuration_status': configuration_status,
                        'error_code': error_code,
                        'error_message': error_message,
                        'ret_post': ret_post,
                        'query_filter': query_filter
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
                            'current_page': 'administration/configuration'
        
                    })

    @tornado.web.asynchronous
    def post(self, ganeshd_host, ganeshd_port, category = None):
        run_background(self.post_configuration, self.async_callback, (ganeshd_host, ganeshd_port, category))


class AdminConfigurationFileHandler(BaseHandler):
    def get_configuration_file(self, ganeshd_host, ganeshd_port):
        dashboard_info = None
        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))

        if not xsession:
            return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
        try:
            # Get host & PG instance informations.
            dashboard_info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            # Load file content.
            file_content = ganeshd_get_file_content(self.ssl_ca_cert_file, self.file_type, ganeshd['host'], ganeshd['port'], xsession)
            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'edit_file.html',
                    data = {
                        'file_type': self.file_type,
                        'info': dashboard_info,
                        'file_content': file_content,
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'xsession': xsession,
                        'servers': GANESHD_SERVERS,
                        'current_page': 'administration/%s' % (self.file_type,)
                    })
        except GaneshdError as e:
            if e.code == 401:
                return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")
            else:
                return HTMLAsyncResult(
                        http_code = e.code,
                        template_file = 'error.html',
                        data= {
                            'code': str(e.code),
                            'message': str(e.message),
                            'info': dashboard_info,
                            'ganeshd_host': ganeshd['host'],
                            'ganeshd_port': ganeshd['port'],
                            'xsession': xsession,
                            'servers': GANESHD_SERVERS,
                            'current_page': 'administration/%s' % (self.file_type,)
                        })

    @tornado.web.asynchronous
    def get(self, ganeshd_host, ganeshd_port):
        run_background(self.get_configuration_file, self.async_callback, (ganeshd_host, ganeshd_port))

    def post_configuration_file(self, ganeshd_host, ganeshd_port):
        error_code = None
        error_message = None
        ret_post = None
        dashboard_info = None

        ganeshd = get_ganeshd_server(ganeshd_host, ganeshd_port)
        xsession = self.get_secure_cookie("ganesh_"+ganeshd['host']+"_"+str(ganeshd['port']))

        if not xsession:
            return HTMLAsyncResult(http_code = 401, redirection = "/server/"+ganeshd['host']+"/"+str(ganeshd['port'])+"/login")

        try:
            try:
                # Send file content ..
                ret_post = ganeshd_post_file_content(self.ssl_ca_cert_file, self.file_type, ganeshd['host'], ganeshd['port'], xsession, {'content': self.request.arguments['content']})
                # .. and reload configuration.
                ret_post = ganeshd_post_administration_control(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession, {'action': 'reload'})
            except GaneshdError as e:
                error_code = e.code
                error_message = e.message
            # Load informations.
            dashboard_info = ganeshd_dashboard_info(self.ssl_ca_cert_file, ganeshd['host'], ganeshd['port'], xsession)
            # Load file content.
            file_content = ganeshd_get_file_content(self.ssl_ca_cert_file, self.file_type, ganeshd['host'], ganeshd['port'], xsession)

            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'edit_file.html',
                    data = {
                        'file_type': self.file_type,
                        'info': dashboard_info,
                        'file_content': file_content,
                        'ganeshd_host': ganeshd['host'],
                        'ganeshd_port': ganeshd['port'],
                        'error_code': error_code,
                        'error_message': error_message,
                        'xsession': xsession,
                        'servers': GANESHD_SERVERS,
                        'current_page': 'administration/%s' % (self.file_type,),
                        'ret_post': ret_post
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
                            'current_page': 'administration/%s' % (self.file_type,)
                        })

    @tornado.web.asynchronous
    def post(self, ganeshd_host, ganeshd_port):
        run_background(self.post_configuration_file, self.async_callback, (ganeshd_host, ganeshd_port))

class AdminHBAHandler(AdminConfigurationFileHandler):
    file_type = 'hba'

class AdminPGIdentHandler(AdminConfigurationFileHandler):
    file_type = 'pg_ident'
