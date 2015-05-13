import httplib, urllib
import json

class GaneshdError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message

def ganeshd_login(hostname, port, username, password):
    params = json.dumps({'username': username, 'password': password})
    headers = {"Content-type": "application/json"}
    conn = httplib.HTTPConnection(hostname, port)
    conn.request("POST", "/login", params, headers)
    response = conn.getresponse()
    conn.close()
    data = response.read()
    if response.status == 200:
        xsession = json.loads(data)['session']
        return xsession
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_dashboard(hostname, port, xsession):
    params = None
    headers = {"X-Session": xsession}
    conn = httplib.HTTPConnection(hostname, port)
    conn.request("GET", "/dashboard", params, headers)
    response = conn.getresponse()
    conn.close()
    data = response.read()
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])
