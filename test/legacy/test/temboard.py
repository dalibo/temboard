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

import configtest as test_conf

# Add main temboard-agent module dir into sys.path
# The goal is to import spc module
tbda_dir = os.path.realpath(
            os.path.join(__file__, '..', '..', '..', '..'))

if tbda_dir not in sys.path:
    sys.path.insert(0, tbda_dir)

from temboardagent.spc import connector, error  # noqa


def exec_command(command_args, comm=True, **kwargs):
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

    if comm:
        (stdout, stderrout) = process.communicate()
        return (process.returncode, stdout, stderrout)
    else:
        return process


def pg_init(pg_bin, pg_data, pg_settings):
    """
    Create a new PostgreSQL cluster using initdb.
    """
    (ret_code, stdout, stderr) = exec_command([
                                    pg_bin+"/initdb",
                                    "-D",
                                    pg_data])
    if ret_code != 0:
        raise Exception(str(stderr))
    with open(pg_data+"/postgresql.conf", "a") as fd:
        fd.writelines(pg_settings)
        fd.close()


def pg_start(pg_bin, pg_port, pg_socket_dir, pg_data, pg_log_file_path):
    """
    Start PostgreSQL
    """
    cmd = '%s/pg_ctl start -D %s -l %s -o "-p%s -k%s"' % (
            pg_bin,
            pg_data,
            pg_log_file_path,
            pg_port,
            pg_socket_dir
            )
    exec_command(cmd, comm=False, shell=True)
    time.sleep(1)


def pg_stop(pg_bin, pg_port, pg_socket_dir, pg_data):
    """
    Stop immediately the PostgreSQL cluster.
    """
    cmd = '%s/pg_ctl stop -m immediate -D %s -o "-p%s -k%s"' % (
            pg_bin,
            pg_data,
            pg_port,
            pg_socket_dir
            )
    exec_command(cmd, comm=False, shell=True)


def pg_drop(pg_data):
    """
    Remove PostgreSQL data directory.
    """
    # /!\ WARNING: This is VERY dangerous /!\
    # TODO: Find a safer way to drop the data directory.
    (ret_code, stdout, stderr) = exec_command(["rm", "-rf", pg_data])
    if ret_code != 0:
        raise Exception(str(stderr))


def pg_add_super_user(pg_bin, pg_user, pg_host, pg_port, pg_password=''):
    """
    Create a new PostgreSQL super-user.
    """
    (ret_code, stdout, stderr) = exec_command([
                                    pg_bin+"/createuser",
                                    "-h", pg_host,
                                    "-p", pg_port,
                                    "-ls", pg_user])
    if ret_code != 0:
        raise Exception(str(stderr))

    conn = connector(host=pg_host,
                     port=pg_port,
                     user=pg_user,
                     database='postgres')

    if len(pg_password) > 0:
        try:
            conn.connect()
            query = "ALTER USER %s PASSWORD '%s'" % (
                        pg_user,
                        pg_password
                        )
            conn.execute(query)
            conn.close()
        except error as e:
            raise Exception(str(e.message))


def agent_add_user(passwd_file_path, user, passwd):
    """
    Add a new temboard-agent user.
    """
    (ret_code, stdout, stderr) = exec_command([
                                    "temboard-agent-password",
                                    "%s:%s" % (user, passwd)])
    if ret_code != 0:
        raise Exception(str(stderr))

    with open(passwd_file_path, "a") as fd:
        fd.write(stdout)


def agent_write_conf(conf_tpl, test_env):
    """
    Write agent's configuration file.
    """
    with open(test_env['agent']['conf_file'], 'w') as fd:
        fd.write(conf_tpl % (
            test_env['agent']['port'],
            test_env['agent']['users'],
            test_env['agent']['ssl_key_file'],
            test_env['agent']['ssl_cert_file'],
            test_env['agent']['home'],
            test_env['pg']['socket_dir'],
            test_env['pg']['port'],
            test_env['pg']['user'],
            test_env['pg']['password'],
            test_env['agent']['log_file'],
            test_env['agent']['ssl_cert_file']))


def agent_start(pid_file, conf_file):
    """
    Start the agent.
    """
    cmd = "temboard-agent -c %s -d -p %s" % (
            conf_file,
            pid_file
            )

    retcode, stdout, stderr = exec_command(cmd, comm=True, shell=True)
    assert retcode == 0, stderr


def agent_stop(pid_file):
    """
    Stop the agent.
    """
    with open(pid_file, 'r') as fd:
        pid = fd.read()
    # Stop it using kill()
    os.kill(int(pid), signal.SIGTERM)


def agent_write_ssl_files(key_file, key_content, cert_file, cert_content):
    """
    Write SSL files
    """
    # Key file
    with open(key_file, 'w') as fd:
        fd.write(key_content)
    # Cert. file
    with open(cert_file, 'w') as fd:
        fd.write(cert_content)


def _mkdir(path):
    """
    Create a directory and its parents is they do not exist.
    Returns the path.
    """
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
    """
    Testing environnement setup:
        * creation of the tree directory
        * write configuration files
        * PostgreSQL cluster initdb
        * start PostgreSQL cluster and agent
    """

    # Overwrite some variables from testconfig.py by env. variables.

    # PostgreSQL binaries path
    tbd_pgbin = test_conf.PG_BIN
    if 'TBD_PGBIN' in os.environ:
        tbd_pgbin = os.environ['TBD_PGBIN']

    # PostgreSQL port
    tbd_pgport = test_conf.PG_PORT
    if 'TBD_PGPORT' in os.environ:
        tbd_pgport = os.environ['TBD_PGPORT']
    # Work path
    tbd_workpath = test_conf.WORK_PATH
    if 'TBD_WORKPATH' in os.environ:
        tbd_workpath = os.environ['TBD_WORKPATH']

    test_env = {
        'agent': {
            'conf_file': None,
            'pid_file': None,
            'users': None,
            'home': None,
            'log_file': None,
            'ssl_cert_file': None,
            'ssl_ca_cert_file': None,
            'ssl_key_file': None,
            'host': test_conf.AGENT_HOST,
            'port': str(test_conf.AGENT_PORT),
            'user': test_conf.AGENT_USER,
            'password': test_conf.AGENT_PASSWORD,
        },
        'pg': {
            'bin': tbd_pgbin,
            'pg_data': None,
            'socket_dir': None,
            'port': str(tbd_pgport),
            'user': test_conf.PG_USER,
            'password': test_conf.PG_PASSWORD,
            'log_file': None
        }
    }
    try:
        ext = str(int(time.time() * 1000))
        # Folders creation
        root_dir = _mkdir(tbd_workpath+'/tests_temboard/'+ext)
        agent_dir = _mkdir(root_dir+'/temboard-agent')
        log_dir = _mkdir(root_dir+'/logs')

        # PG env. vars
        test_env['pg']['pg_data'] = _mkdir(root_dir+'/pg/data')
        test_env['pg']['socket_dir'] = _mkdir(root_dir+'/pg/run')
        test_env['pg']['log_file'] = log_dir+'/postgresql.log'

        # agent env. vars
        test_env['agent']['conf_file'] = agent_dir+'/temboard-agent.conf'
        test_env['agent']['pid_file'] = agent_dir+'/temboard-agent.pid'
        test_env['agent']['users'] = agent_dir+'/users'
        test_env['agent']['log_file'] = log_dir+'/temboard-agent.log'
        test_env['agent']['ssl_key_file'] = agent_dir+'/temboard-agent.key'
        test_env['agent']['ssl_cert_file'] = agent_dir+'/temboard-agent.pem'
        test_env['agent']['ssl_ca_cert_file'] = agent_dir+'/temboard-agent.pem'
        test_env['agent']['home'] = _mkdir(agent_dir+'/home')

        # PG Cluster creation
        pg_init(test_env['pg']['bin'],
                test_env['pg']['pg_data'],
                test_conf.PG_SETTINGS)
        # Let's start the PG cluster
        pg_start(test_env['pg']['bin'],
                 test_env['pg']['port'],
                 test_env['pg']['socket_dir'],
                 test_env['pg']['pg_data'],
                 test_env['pg']['log_file'])
        # Sleep a bit
        time.sleep(1)
        # Super-user creation.
        pg_add_super_user(test_env['pg']['bin'],
                          test_env['pg']['user'],
                          test_env['pg']['socket_dir'],
                          test_env['pg']['port'],
                          test_env['pg']['password'])
        # Agent user creation.
        agent_add_user(test_env['agent']['users'],
                       test_env['agent']['user'],
                       test_env['agent']['password'])
        # Write SSL files.
        agent_write_ssl_files(test_env['agent']['ssl_key_file'],
                              test_conf.AGENT_SSL_KEY,
                              test_env['agent']['ssl_cert_file'],
                              test_conf.AGENT_SSL_CERT)
        # Write agent configuration file.
        agent_write_conf(test_conf.AGENT_CONFIG,
                         test_env)
        # Start the agent
        agent_start(test_env['agent']['pid_file'],
                    test_env['agent']['conf_file'])
        return test_env
    except Exception as e:
        # If anything goes wrong during the setup
        # then we drop the whole testing environnement.
        drop_env(test_env)
        raise Exception(e)


def drop_env(test_env):
    """
    Try to stop the components and delete PG data dir.
    """
    try:
        # Try to stop the agent.
        agent_stop(test_env['agent']['pid_file'])
    except Exception:
        pass
    try:
        # Try to stop PG cluster
        pg_stop(test_env['pg']['bin'],
                test_env['pg']['port'],
                test_env['pg']['socket_dir'],
                test_env['pg']['pg_data'])
        # Wait a second before trying to remove the data dir
        time.sleep(1)
        # Remove PostgreSQL data dir
        pg_drop(test_env['pg']['pg_data'])
    except Exception:
        pass


def rand_string(n):
    """
    Return a random string.
    """
    return ''.join(
            random.SystemRandom().choice(
                string.ascii_lowercase + string.digits) for _ in range(n))


"""
HTTPS client part
"""


class VerifiedHTTPSConnection(httplib.HTTPSConnection):
    """
    HTTPS connector using a specified CA CERT file.
    """
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
    """
    HTTPS handler overwriting urllib2.HTTPSHandler class.
    """
    def __init__(self, connection_class=VerifiedHTTPSConnection):
        self.specialized_conn_class = connection_class
        urllib2.HTTPSHandler.__init__(self)

    def https_open(self, req):
        return self.do_open(self.specialized_conn_class, req)


class RequestWithMethod(urllib2.Request):
    """
    HTTP Request with method (GET,POST,DELETE,etc...)
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return super(RequestWithMethod, self).get_method()


def temboard_request(in_ca_cert_file, method, url, headers=None, data=None):
    """
    Temboard agent client.
    """
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
    try:
        handle = url_opener.open(request)
        response = handle.read()
        handle.close()
    except urllib2.HTTPError as e:
        if sys.version < (2, 7, 0):
            return (e.code, json.dumps({'error': e.code}))
        else:
            return (e.code, json.dumps({'error': e.reason}))
    return (handle.code, response)
