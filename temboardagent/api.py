import time
import pickle
import base64

from temboardagent.routing import add_route
from temboardagent.errors import (HTTPError, SharedItem_exists,
                            SharedItem_no_free_slot_left, SharedItem_not_found,
                            NotificationError)
from temboardagent.sharedmemory import Session, Command
from temboardagent.types import *
from temboardagent.tools import validate_parameters, hash_id
from temboardagent.usermgmt import auth_user, gen_sessionid
from temboardagent.logger import get_logger, set_logger_name, get_tb
from temboardagent.spc import connector, error
from temboardagent.command import exec_command
from temboardagent.workers import COMMAND_START, COMMAND_DONE, COMMAND_ERROR
from temboardagent.notification import NotificationMgmt, Notification
from temboardagent.inventory import *

def check_sessionid(http_header, sessions):
    validate_parameters(http_header,
        [('X-Session', T_SESSIONID, False)])
    try:
        session = sessions.get_by_sessionid(http_header['X-Session'].encode('utf-8'))
        session.time = time.time()
        username = session.username
        sessions.update(session)
        return username
    except SharedItem_not_found:
        raise HTTPError(401, "Invalid session.")

"""
HTTP REST API
v0.0.1
"""

@add_route('POST', '/login')
def login(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /login User login
    @apiVersion 0.0.1
    @apiName UserLogin
    @apiGroup User

    @apiParam {String} username Username.
    @apiParam {String} password Password.

    @apiSuccess {String} sessions Session ID.

    @apiExample {curl} Example usage:
        curl -k -X POST -H "Content-Type: application/json" -d '{"username": "julien", "password": "password12!"}' \
            https://localhost:2345/login

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:19:48 GMT
        Content-type: application/json

        {"session": "fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63"}

    @apiError (500 error) error Internal error.
    @apiError (404 error) error Invalid username or password.
    @apiError (406 error) error Username or password malformed or missing.

    @apiErrorExample 404 error example
        HTTP/1.0 404 Not Found
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:20:33 GMT
        Content-type: application/json

        {"error": "Invalid username/password."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:21:01 GMT
        Content-type: application/json

        {"error": "Parameter 'password' is malformed."}
    """
    post = http_context['post']
    set_logger_name("api")
    logger = get_logger(config)
    # Add an unconditional sleeping time to reduce brute-force risks
    time.sleep(1)

    logger.info("Authenticating user: %s" % (post['username']))
    try:
        validate_parameters(post,
            [('username', T_USERNAME, False),
            ('password', T_PASSWORD, False)])
        auth_user(config.temboard['users'], post['username'],
                post['password'])
    except HTTPError as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Authentication failed.")
        raise e
    try:
        session = sessions.get_by_username(post['username'])
        if not session:
            sessionid = gen_sessionid(post['username'])
            session = Session(sessionid.encode('utf-8'), time.time(), post['username'].encode('utf-8'))
            sessions.add(session)
        else:
            sessionid = session.sessionid
            session.time = time.time()
            sessions.update(session)
        try:
            NotificationMgmt.push(config, Notification(
                                        username = post['username'],
                                        message = "Login"))
        except NotificationError as e:
            logger.traceback(get_tb())
            logger.error(e.message)

    except (SharedItem_exists, SharedItem_no_free_slot_left) as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        raise HTTPError(500, "Internal error.")
    return {'session': sessionid}

@add_route('GET', '/logout')
def logout(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /logout User logout
    @apiVersion 0.0.1
    @apiName UserLogout
    @apiGroup User

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Bool} logout True if logout succeeds.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63" https://localhost:2345/logout

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:33:19 GMT
        Content-type: application/json

        {"logout": true}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session ID.
    @apiError (406 error) error Session ID malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:36:33 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:37:23 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}
    """
    headers = http_context['headers']
    set_logger_name("api")
    logger = get_logger(config)
    logger.info("Removing session: %s" % (headers['X-Session']))
    try:
        username = check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Invalid session.")
        raise e

    try:
        NotificationMgmt.push(config, Notification(
                                        username = username,
                                        message = "Logout"))
    except NotificationError as e:
        logger.traceback(get_tb())
        logger.error(e.message)

    try:
        sessions.delete(headers['X-Session'].encode('utf-8'))
    except (SharedItem_exists, SharedItem_no_free_slot_left) as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        raise HTTPError(500, "Internal error.")
    return {'logout': True}


@add_route('GET', '/discover')
def get_discover(http_contexte, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /discover Get global informations about the env.
    @apiVersion 0.0.1
    @apiName Discover
    @apiGroup User

    @apiSuccess {String}   hostname Hostname.
    @apiSuccess {String}   pg_data PostgreSQL data directory.
    @apiSuccess {Number}   pg_port PostgreSQL listen port.
    @apiSuccess {String}   pg_version PostgreSQL version.
    @apiSuccess {String[]} plugins List or available plugins.
    @apiSuccess {Number}   memory_size Memory size (bytes).
    @apiSuccess {Number}   cpu Number of CPU.

    @apiExample {curl} Example usage:
        curl -k https://localhost:2345/discover

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:33:19 GMT
        Content-type: application/json
        {
            "hostname": "neptune",
            "pg_data": "/var/lib/postgresql/9.4/main",
            "pg_port": 5432,
            "plugins": ["monitoring", "dashboard", "pgconf",
                        "administration", "activity"],
            "memory_size": 8241508352,
            "pg_version": "PostgreSQL 9.4.5 on x86_64-unknown-linux-gnu, compiled by gcc (Ubuntu 4.9.2-10ubuntu13) 4.9.2, 64-bit",
            "cpu": 4
        }

    @apiError (500 error) error Internal error.
    """  # noqa
    set_logger_name("api")
    logger = get_logger(config)
    conn = connector(
        host = config.postgresql['host'],
        port = config.postgresql['port'],
        user = config.postgresql['user'],
        password = config.postgresql['password'],
        database = config.postgresql['dbname']
    )
    logger.info('Starting discovery.')
    try:
        conn.connect()
        sysinfo = SysInfo()
        pginfo = PgInfo(conn)
        ret = {
            'hostname': sysinfo.hostname(config.temboard['hostname']),
            'cpu': sysinfo.n_cpu(),
            'memory_size': sysinfo.memory_size(),
            'pg_port': pginfo.setting('port'),
            'pg_version': pginfo.version()['full'],
            'pg_data': pginfo.setting('data_directory'),
            'plugins': [plugin_name for plugin_name in config.temboard['plugins']]
        }
        conn.close()
        logger.info('Discovery done.')
        return ret

    except (error, Exception, HTTPError) as e:
        logger.traceback(get_tb())
        logger.error(str(e))
        logger.info('Discovery failed.')
        try:
            conn.close()
        except Exception:
            pass
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")

@add_route('GET', '/profile')
def profile(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /profile Get current user name.
    @apiVersion 0.0.1
    @apiName Profile
    @apiGroup User

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {String} username Username.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63" https://localhost:2345/profile

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:33:19 GMT
        Content-type: application/json
        {
            "username": "julien"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session ID.
    @apiError (406 error) error Session ID malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:36:33 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:37:23 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}
    """
    headers = http_context['headers']
    set_logger_name("api")
    logger = get_logger(config)
    logger.info("Get user profile.")
    try:
        check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Invalid session.")
        raise e
    try:
        session = sessions.get_by_sessionid(headers['X-Session'].encode('utf-8'))
        logger.info("Done.")
        return {'username': session.username}
    except SharedItem_not_found as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Failed.")
        raise HTTPError(401, "Invalid session.")

@add_route('GET', '/command/'+T_COMMANDID)
def get_command(http_context, queue_in = None, config = None, sessions = None, commands = None):
    headers = http_context['headers']
    set_logger_name("api")
    logger = get_logger(config)
    logger.info("Get command status.")
    try:
        check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Invalid session.")
        raise e
    cid = http_context['urlvars'][0]
    try:
        command = commands.get_by_commandid(cid.encode('utf-8'))
        c_time = command.time
        c_state = command.state
        c_result = command.result
        if c_state == COMMAND_DONE or c_state == COMMAND_ERROR:
            commands.delete(cid.encode('utf-8'))
        logger.info("Done.")
        return {'cid': cid, 'time': c_time, 'state': c_state, 'result': c_result}
    except SharedItem_not_found as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Failed.")
        raise HTTPError(401, "Invalid command.")

@add_route('GET', '/notifications')
def notifications(http_context, queue_in = None, config = None, sessions = None, commands = None):
    """
    @api {get} /notifications Get all notifications.
    @apiVersion 0.0.1
    @apiName Notifications
    @apiGroup User

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object[]} notifications List of notifications.
    @apiSuccess {String}   notifications.date Notification datetime.
    @apiSuccess {String}   notifications.username Username.
    @apiSuccess {String}   notifications.message Message.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63" https://localhost:2345/notifications

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:33:19 GMT
        Content-type: application/json

        [
            {"date": "2016-04-11T16:12:38", "username": "julien", "message": "Login"},
            {"date": "2016-04-11T16:02:03", "username": "julien", "message": "Login"},
            {"date": "2016-04-11T15:51:15", "username": "julien", "message": "HBA file version '2016-04-11T15:32:53' removed."},
            {"date": "2016-04-11T15:51:10", "username": "julien", "message": "HBA file version '2016-04-11T15:47:26' removed."},
            {"date": "2016-04-11T15:51:04", "username": "julien", "message": "HBA file version '2016-04-11T15:48:50' removed."},
            {"date": "2016-04-11T15:50:57", "username": "julien", "message": "PostgreSQL reload"},
            {"date": "2016-04-11T15:50:57", "username": "julien", "message": "HBA file updated"},
            {"date": "2016-04-11T15:48:50", "username": "julien", "message": "PostgreSQL reload"}
        ]

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session ID.
    @apiError (406 error) error Session ID malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:36:33 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 12:37:23 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}
    """
    headers = http_context['headers']
    set_logger_name("api")
    logger = get_logger(config)
    logger.info("Get notifications.")
    try:
        username = check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Invalid session.")
        raise e

    try:
        notifications = NotificationMgmt.get_last_n(config, -1)
        logger.info("Done.")
        return list(notifications)
    except (NotificationError, Exception) as e:
        logger.traceback(get_tb())
        logger.error(e.message)
        logger.info("Failed.")
        raise HTTPError(500, "Internal error.")
