import httplib
import urllib2
from urllib import quote
import ssl
import socket
import json


class VerifiedHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(
            sock,
            self.key_file,
            self.cert_file,
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=CA_CERT_FILE)


class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
    def __init__(self, connection_class=VerifiedHTTPSConnection):
        self.specialized_conn_class = connection_class
        urllib2.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.specialized_conn_class, req)


class RequestWithMethod(urllib2.Request):
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method if self._method else super(RequestWithMethod,
                                                       self).get_method()


def temboard_request(in_ca_cert_file, method, url, headers=None, data=None):
    global CA_CERT_FILE
    CA_CERT_FILE = in_ca_cert_file
    https_handler = VerifiedHTTPSHandler()
    url_opener = urllib2.build_opener(https_handler)
    headers_list = []
    for key, val in headers.iteritems():
        headers_list.append((key, val))
    url_opener.addheaders = headers_list
    if data:
        request = RequestWithMethod(url, data=json.dumps(data), method=method)
    else:
        request = RequestWithMethod(url, method=method)
    handle = url_opener.open(request)
    response = handle.read()
    handle.close()
    return response


class TemboardError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def temboard_login(in_ca_cert_file, hostname, port, username, password):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='POST',
            url='https://%s:%s/login' % (hostname, port),
            headers={"Content-type": "application/json"},
            data={'username': username,
                  'password': password})
        return json.loads(res)['session']
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_dashboard(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/dashboard' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_dashboard_history(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/dashboard/history' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_dashboard_live(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/dashboard/live' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_dashboard_info(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/dashboard/info' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_configuration(in_ca_cert_file,
                               hostname,
                               port,
                               xsession,
                               enc_category=None,
                               query_filter=None):
    try:
        if query_filter:
            path = "/pgconf/configuration?filter=" + quote(query_filter)
        elif enc_category:
            path = "/pgconf/configuration/category/" + enc_category
        else:
            path = "/pgconf/configuration"
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s%s' % (hostname, port, path),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_post_configuration(in_ca_cert_file, hostname, port, xsession,
                                settings):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='POST',
            url='https://%s:%s/pgconf/configuration' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            },
            data=settings)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_configuration_categories(in_ca_cert_file, hostname, port,
                                          xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/pgconf/configuration/categories' % (hostname,
                                                                   port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_configuration_status(in_ca_cert_file, hostname, port,
                                      xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/pgconf/configuration/status' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_post_administration_control(in_ca_cert_file, hostname, port,
                                         xsession, action):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='POST',
            url='https://%s:%s/administration/control' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            },
            data=action)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_file_content(in_ca_cert_file, file_type, hostname, port,
                              xsession):
    file_types = {'hba': '/pgconf/hba/raw', 'pg_ident': '/pgconf/pg_ident'}
    if file_type not in file_types:
        raise TemboardError(404, 'Unknown file_type.')
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s%s' % (hostname, port, file_types[file_type]),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_post_file_content(in_ca_cert_file, file_type, hostname, port,
                               xsession, content):
    file_types = {'hba': '/pgconf/hba/raw', 'pg_ident': '/pgconf/pg_ident'}
    if file_type not in file_types:
        raise TemboardError(404, 'Unknown file_type.')
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='POST',
            url='https://%s:%s%s' % (hostname, port, file_types[file_type]),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            },
            data=content)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, e.message)


def temboard_activity(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/activity' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_activity_waiting(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/activity/waiting' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_activity_blocking(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/activity/blocking' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_activity_kill(in_ca_cert_file, hostname, port, xsession, pids):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='POST',
            url='https://%s:%s/activity/kill' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            },
            data=pids)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_discover(in_ca_cert_file, hostname, port):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/discover' % (hostname, port),
            headers={"Content-type": "application/json"})
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_profile(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/profile' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_conf_file_versions(in_ca_cert_file, file_type, hostname, port,
                                    xsession):
    file_types = {'hba': '/pgconf/hba/versions'}
    if file_type not in file_types:
        raise TemboardError(404, 'Unknown file_type.')
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s%s' % (hostname, port, file_types[file_type]),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_conf_file(in_ca_cert_file, file_type, version, hostname, port,
                           xsession):
    file_types = {'hba': '/pgconf/hba'}
    if file_type not in file_types:
        raise TemboardError(404, 'Unknown file_type.')
    p_version = ''
    if version is not None:
        p_version = "?version=%s" % (version)
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s%s%s' % (hostname, port, file_types[file_type],
                                       p_version),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_conf_file_raw(in_ca_cert_file, file_type, version, hostname,
                               port, xsession):
    file_types = {'hba': '/pgconf/hba/raw'}
    if file_type not in file_types:
        raise TemboardError(404, 'Unknown file_type.')
    p_version = ''
    if version is not None:
        p_version = "?version=%s" % (version)
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s%s%s' % (hostname, port, file_types[file_type],
                                       p_version),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_hba_options(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/pgconf/hba/options' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_post_conf_file(in_ca_cert_file, file_type, hostname, port,
                            xsession, data):
    file_types = {'hba': '/pgconf/hba'}
    if file_type not in file_types:
        raise TemboardError(404, 'Unknown file_type.')
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='POST',
            url='https://%s:%s%s' % (hostname, port, file_types[file_type]),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            },
            data=data)
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_delete_hba_version(in_ca_cert_file, hostname, port, xsession,
                                version):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='DELETE',
            url='https://%s:%s/pgconf/hba?version=%s' % (hostname, port,
                                                         version),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_get_notifications(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://%s:%s/notifications' % (hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib2.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))
