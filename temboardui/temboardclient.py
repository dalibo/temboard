import http.client
import urllib
import urllib.error
import urllib.request
import ssl
import socket
import json


class VerifiedHTTPSConnection(http.client.HTTPSConnection):
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


class VerifiedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, connection_class=VerifiedHTTPSConnection):
        self.specialized_conn_class = connection_class
        urllib.request.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.specialized_conn_class, req)


class UnverifiedHTTPSConnection(http.client.HTTPSConnection):
    # HTTPS connection class, without any SSL cert. check.
    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(sock)


class UnverifiedHTTPSHandler(urllib.request.HTTPSHandler):
    # HTTPS connection handler
    def __init__(self, connection_class=UnverifiedHTTPSConnection):
        self.specialized_conn_class = connection_class
        urllib.request.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.specialized_conn_class, req)


class RequestWithMethod(urllib.request.Request):
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method if self._method else super().get_method()


def temboard_request(in_ca_cert_file, method, url, headers=None, data=None):
    global CA_CERT_FILE
    CA_CERT_FILE = in_ca_cert_file
    if in_ca_cert_file is None:
        https_handler = UnverifiedHTTPSHandler()
    else:
        https_handler = VerifiedHTTPSHandler()
    url_opener = urllib.request.build_opener(https_handler)
    headers_list = []
    for key, val in headers.items():
        headers_list.append((key, val))
    url_opener.addheaders = headers_list
    if data is not None:
        request = RequestWithMethod(
            url, data=json.dumps(data).encode("utf-8"), method=method)
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


def temboard_discover(in_ca_cert_file, hostname, port):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://{}:{}/discover'.format(hostname, port),
            headers={"Content-type": "application/json"})
        return json.loads(res)
    except urllib.error.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))


def temboard_profile(in_ca_cert_file, hostname, port, xsession):
    try:
        res = temboard_request(
            in_ca_cert_file,
            method='GET',
            url='https://{}:{}/profile'.format(hostname, port),
            headers={
                "Content-type": "application/json",
                "X-Session": xsession
            })
        return json.loads(res)
    except urllib.error.HTTPError as e:
        raise TemboardError(e.code, json.loads(e.read())['error'])
    except Exception as e:
        raise TemboardError(500, str(e))
