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
    try:
        conn = httplib.HTTPConnection(hostname, port)
        conn.request("POST", "/login", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))
    if response.status == 200:
        xsession = json.loads(data)['session']
        return xsession
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_dashboard(hostname, port, xsession):
    params = None
    headers = {"X-Session": xsession}
    try:
        conn = httplib.HTTPConnection(hostname, port)
        conn.request("GET", "/dashboard", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_get_configuration(hostname, port, xsession, enc_category = None):
    params = None
    headers = {"X-Session": xsession}
    try:
        conn = httplib.HTTPConnection(hostname, port)
        if enc_category:
            conn.request("GET", "/administration/configuration/category/"+enc_category, params, headers)
        else:
            conn.request("GET", "/administration/configuration", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_post_configuration(hostname, port, xsession, settings):
    params = json.dumps(settings)
    headers = {"X-Session": xsession}
    conn = httplib.HTTPConnection(hostname, port)
    conn.request("POST", "/administration/configuration", params, headers)
    response = conn.getresponse()
    conn.close()
    data = response.read()
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_get_configuration_categories(hostname, port, xsession):
    params = None
    headers = {"X-Session": xsession}
    try:
        conn = httplib.HTTPConnection(hostname, port)
        conn.request("GET", "/administration/configuration/categories", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_get_configuration_status(hostname, port, xsession):
    params = None
    headers = {"X-Session": xsession}
    conn = httplib.HTTPConnection(hostname, port)
    try:
        conn.request("GET", "/administration/configuration/status", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))

    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_post_administration_control(hostname, port, xsession, action):
    params = json.dumps(action)
    headers = {"X-Session": xsession}
    try:
        conn = httplib.HTTPConnection(hostname, port)
        conn.request("POST", "/administration/control", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])

def ganeshd_dashboard_info(hostname, port, xsession):
    params = None
    headers = {"X-Session": xsession}
    try:
        conn = httplib.HTTPConnection(hostname, port)
        conn.request("GET", "/dashboard/info", params, headers)
        response = conn.getresponse()
        conn.close()
        data = response.read()
    except Exception as e:
        raise GaneshdError(500, str(e))
    if response.status == 200:
        return json.loads(data)
    else:
        raise GaneshdError(response.status, json.loads(data)['error'])
