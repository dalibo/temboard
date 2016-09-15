from __future__ import print_function
import time
import os
import sys
import signal
import random
import string
from subprocess import Popen, PIPE
import httplib
import urllib2
import ssl
import socket
import json

import test.configuration as cf
from test.spc import connector, error

def exec_command(command_args, comm = True, **kwargs):
    """
    Execute a system command with Popen.
    """
    kwargs.setdefault("stdout", PIPE)
    kwargs.setdefault("stderr", PIPE)
    kwargs.setdefault("stdin", PIPE)
    kwargs.setdefault("close_fds", True)
    try:
        process = Popen(command_args, **kwargs)
    except OSError as err:
        return (err.errno, None, err.strerror)

    if comm is True:
        (stdout, stderrout) = process.communicate()
        return (process.returncode, stdout, stderrout)

def pg_init(pg_bin, pg_data):
    (ret_code, stdout, stderr) = exec_command([pg_bin+"/initdb", "-D", pg_data])
    if ret_code != 0:
        raise Exception(str(stderr))
    with open(pg_data+"/postgresql.conf", "a") as fd:
        fd.writelines(cf.PG_CONF)
        fd.close()

def pg_start(pg_bin, pg_port, pg_sockdir, pg_data, pg_log_file_path):
    exec_command(pg_bin+"/pg_ctl start -D %s -l %s -o \"-p%s -k%s\"" %
                    (pg_data, pg_log_file_path, str(pg_port), pg_sockdir),
                comm = False, shell = True)
    time.sleep(1)

def pg_stop(pg_bin, pg_port, pg_sockdir, pg_data):
    exec_command(pg_bin+"/pg_ctl stop -m fast -D "+pg_data+" -o \"-p%s -k%s\"" %
        (pg_port, pg_sockdir), comm = False, shell = True)

def pg_drop(pg_data):
    (ret_code, stdout, stderr) = exec_command(["rm", "-rf", pg_data])
    if ret_code != 0:
        raise Exception(str(stderr))

def pg_add_super_user(pg_bin, pg_user, pg_host, pg_port, pg_password = ''):
    (ret_code, stdout, stderr) = exec_command([pg_bin+"/createuser", "-h",
                                    pg_host, "-p", pg_port, "-ls", pg_user])
    if ret_code != 0:
        raise Exception(str(stderr))
    conn = connector(host = pg_host, port = pg_port, user = pg_user, database = 'postgres')
    if len(pg_password) > 0:
        try:
            conn.connect()
            conn.execute("ALTER USER %s PASSWORD '%s'" % (pg_user, pg_password))
            conn.close()
        except error as e:
            raise Exception(str(e.message))

def g_add_user(g_password_file_path, g_user, g_password, python = "python"):
    (ret_code, stdout, stderr) = exec_command([python, "../temboard-agent-password", "%s:%s"
                                    % (g_user, g_password)])
    if ret_code != 0:
        raise Exception(str(stderr))
    with open(g_password_file_path, "a") as fd:
        fd.write(stdout)

def g_write_conf(g_str_conf, g_conf_file_path,
                    g_port,
                    g_users,
                    g_ssl_key_path,
                    g_ssl_cert_path,
                    g_home,
                    pg_host,
                    pg_port,
                    pg_user,
                    pg_password,
                    g_log_file_path,
                    g_ssl_ca_cert_path):
    with open(g_conf_file_path, "w") as fd:
        fd.write(g_str_conf % (g_port,
                                g_users,
                                g_ssl_key_path,
                                g_ssl_cert_path,
                                g_home,
                                pg_host,
                                pg_port,
                                pg_user,
                                pg_password,
                                g_log_file_path,
                                g_ssl_ca_cert_path))

def g_start(g_pid_file_path, g_conf_file_path, python = "python"):
    exec_command(python+" ../temboard-agent -c %s -d -p %s" %
            (g_conf_file_path, g_pid_file_path), comm = False, shell = True)
    time.sleep(1)

def g_stop(g_pid_file_path):
    with open(g_pid_file_path, 'r') as fd:
        content = fd.read()
    os.kill(int(content), signal.SIGTERM)

def g_build_ssl_cert(key_filepath, key_content, cert_filepath, cert_content):
    with open(key_filepath, "w") as fd:
        fd.write(key_content)
    with open(cert_filepath, "w") as fd:
        fd.write(cert_content)

def _mkdir(path):
    c_path = ''
    for f in path.split('/'):
        c_path += '/' + f
        if not os.path.exists(c_path):
            os.mkdir(c_path)
        elif os.path.exists(c_path) and os.path.isdir(c_path):
            continue
        elif os.path.exists(c_path) and not os.path.isdir(c_path):
            os.mkdir(c_path)
    return path

def init_env():
    env = {
        'pg_data': None,
        'pg_sockdir': None,
        'g_conf_file_path': None,
        'g_pid_file_path': None,
        'g_password_file_path': None,
        'g_log_file_path': None,
        'pg_sockdir': None,
        'pg_log_file_path': None,
        'g_ssl_cert_file_path': None,
        'g_home': None}
    try:
        ext = str(int(time.time() * 1000))
        env['pg_data'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/pg/data')
        env['pg_sockdir'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/pg/run')
        env['g_conf_file_path'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/temboard-agent')+'/temboard-agent.conf'
        env['g_pid_file_path'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/temboard-agent')+'/temboard-agent.pid'
        env['g_password_file_path'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/temboard-agent')+'/users'
        env['g_log_file_path'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/logs')+'/temboard-agent.log'
        env['pg_log_file_path'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/logs')+'/postgresql.log'
        g_ssl_key_file_path = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/temboard-agent')+'/temboard-agent.key'
        env['g_ssl_cert_file_path'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/temboard-agent')+'/temboard-agent.pem'
        env['g_home'] = _mkdir(cf.WORK_PATH+'/tests_temboard/'+ext+'/temboard-agent/home')

        pg_init(cf.PG_BIN, env['pg_data'])
        pg_start(cf.PG_BIN, cf.PG_PORT, env['pg_sockdir'], env['pg_data'], env['pg_log_file_path'])
        time.sleep(1)
        pg_add_super_user(cf.PG_BIN, cf.PG_USER, env['pg_sockdir'], str(cf.PG_PORT), cf.PG_PASSWORD)
        g_add_user(env['g_password_file_path'], cf.G_USER, cf.G_PASSWORD, python = sys.executable)
        g_build_ssl_cert(g_ssl_key_file_path, cf.SSL_KEY, env['g_ssl_cert_file_path'], cf.SSL_CERT)
        g_write_conf(cf.G_CONFIG, env['g_conf_file_path'],
                    cf.G_PORT,
                    env['g_password_file_path'],
                    g_ssl_key_file_path, env['g_ssl_cert_file_path'], env['g_home'],
                    env['pg_sockdir'], cf.PG_PORT, cf.PG_USER, cf.PG_PASSWORD,
                    env['g_log_file_path'], env['g_ssl_cert_file_path'])
        g_start(env['g_pid_file_path'], env['g_conf_file_path'], python = sys.executable)
        return env
    except Exception as e:
        drop_env(env)
        raise Exception(e)

def drop_env(env):
    try:
        g_stop(env['g_pid_file_path'])
    except Exception as e:
        pass
    try:
        pg_stop(cf.PG_BIN, cf.PG_PORT, env['pg_sockdir'], env['pg_data'])
        time.sleep(1)
        pg_drop(env['pg_data'])
    except Exception as e:
        pass

def rand_string(n):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(n))

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

def temboard_request(in_ca_cert_file, method, url, headers = None, data = None):
    global CA_CERT_FILE
    CA_CERT_FILE = in_ca_cert_file
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
    try:
        handle = url_opener.open(request)
        response = handle.read()
        handle.close()
    except urllib2.HTTPError as e:
        if sys.version < (2,7,0):
            return (e.code, json.dumps({'error': e.code}))
        else:
            return (e.code, json.dumps({'error': e.reason}))
    return (handle.code, response)
