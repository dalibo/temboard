import httplib
import urllib2
import ssl
import socket
import json

class VerifiedHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(sock,
                                    self.key_file,
                                    self.cert_file,
                                    cert_reqs=ssl.CERT_REQUIRED,
                                    ca_certs=CA_CERT_FILE)

class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
    def __init__(self, connection_class = VerifiedHTTPSConnection):
        self.specialized_conn_class = connection_class
        urllib2.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.specialized_conn_class, req)

class RequestWithMethod(urllib2.Request):
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method if self._method else super(RequestWithMethod, self).get_method()

def ganeshd_request(method, url, headers = None, data = None):
    https_handler = VerifiedHTTPSHandler()
    url_opener = urllib2.build_opener(https_handler)
    headers_list = []
    for key, val in headers.iteritems():
        headers_list.append((key,val))
    url_opener.addheaders = headers_list
    if data:
        request = RequestWithMethod(url, data = json.dumps(data), method = method)
    else:
        request = RequestWithMethod(url, method = method)
    handle = url_opener.open(request)
    response = handle.read()
    handle.close()
    return response

CA_CERT_FILE = "/etc/ganesh/ssl/ca_certs.pem"

class GaneshdError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message

def ganeshd_login(hostname, port, username, password):
    try:
        res = ganeshd_request(
                method = 'POST',
                url = 'https://%s:%s/login' % (hostname, port),
                headers = {"Content-type": "application/json"},
                data = {'username': username, 'password': password})
        return json.loads(res)['session']
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_dashboard(hostname, port, xsession):
    try:
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s/dashboard' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_dashboard_info(hostname, port, xsession):
    try:
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s/dashboard/info' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_get_configuration(hostname, port, xsession, enc_category = None, query_filter = None):
    try:
        if query_filter:
            path = "/administration/configuration?filter="+query_filter
        elif enc_category:
            path = "/administration/configuration/category/"+enc_category
        else:
            path = "/administration/configuration"
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s%s' % (hostname, port, path),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_post_configuration(hostname, port, xsession, settings):
    try:
        res = ganeshd_request(
                method = 'POST',
                url = 'https://%s:%s/administration/configuration' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                },
                data = settings)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_get_configuration_categories(hostname, port, xsession):
    try:
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s/administration/configuration/categories' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_get_configuration_status(hostname, port, xsession):
    try:
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s/administration/configuration/status' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_post_administration_control(hostname, port, xsession, action):
    try:
        res = ganeshd_request(
                method = 'POST',
                url = 'https://%s:%s/administration/control' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                },
                data = action)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_get_file_content(file_type, hostname, port, xsession):
    file_types = { 'hba': '/administration/hba', 'pg_ident': '/administration/pg_ident'}
    if file_type not in file_types:
        raise GaneshdError(404, 'Unknown file_type.')
    try:
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s%s' % (hostname, port, file_types[file_type]),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_post_file_content(file_type, hostname, port, xsession, content):
    file_types = { 'hba': '/administration/hba', 'pg_ident': '/administration/pg_ident'}
    if file_type not in file_types:
        raise GaneshdError(404, 'Unknown file_type.')
    try:
        res = ganeshd_request(
                method = 'POST',
                url = 'https://%s:%s%s' % (hostname, port, file_types[file_type]),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                },
                data = content)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_activity(hostname, port, xsession):
    try:
        res = ganeshd_request(
                method = 'GET',
                url = 'https://%s:%s/activity' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))

def ganeshd_activity_kill(hostname, port, xsession, pids):
    try:
        res = ganeshd_request(
                method = 'POST',
                url = 'https://%s:%s/activity/kill' % (hostname, port),
                headers = {
                    "Content-type": "application/json",
                    "X-Session": xsession
                },
                data = pids)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise GaneshdError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise GaneshdError(500, str(e))
