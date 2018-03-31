import logging
import time

from temboardagent.routing import add_route
from temboardagent.errors import (
    HTTPError,
    NotificationError,
    SharedItem_exists,
    SharedItem_no_free_slot_left,
    SharedItem_not_found,
)
from temboardagent.sharedmemory import Session
from temboardagent.types import (
    T_PASSWORD,
    T_SESSIONID,
    T_USERNAME,
)
from temboardagent.tools import validate_parameters
from temboardagent.usermgmt import auth_user, gen_sessionid
from temboardagent.spc import connector, error
from temboardagent.notification import NotificationMgmt, Notification
from temboardagent.inventory import SysInfo, PgInfo


logger = logging.getLogger(__name__)


def check_sessionid(http_header, sessions):
    """
    Check X-Session is valid and the session exists.
    """
    validate_parameters(http_header,
                        [('X-Session', T_SESSIONID, False)])
    try:
        session = sessions.get_by_sessionid(
                    http_header['X-Session'].encode('utf-8'))
        session.time = time.time()
        username = session.username
        sessions.update(session)
        return username
    except SharedItem_not_found:
        raise HTTPError(401, "Invalid session.")


@add_route('POST', '/login')
def login(http_context, config=None, sessions=None):
    post = http_context['post']
    # Add an unconditional sleeping time to reduce brute-force risks
    time.sleep(1)

    logger.info("Authenticating user: %s" % (post['username']))
    try:
        validate_parameters(post,
                            [('username', T_USERNAME, False),
                             ('password', T_PASSWORD, False)])
        auth_user(config.temboard['users'],
                  post['username'],
                  post['password'])
    except HTTPError as e:
        logger.exception(e.message)
        logger.info("Authentication failed.")
        raise e
    try:
        session = sessions.get_by_username(post['username'])
        if not session:
            sessionid = gen_sessionid(post['username'])
            session = Session(sessionid.encode('utf-8'),
                              time.time(),
                              post['username'].encode('utf-8'))
            sessions.add(session)
        else:
            sessionid = session.sessionid
            session.time = time.time()
            sessions.update(session)
        try:
            NotificationMgmt.push(config, Notification(
                                        username=post['username'],
                                        message="Login"))
        except NotificationError as e:
            logger.exception(e.message)

    except (SharedItem_exists, SharedItem_no_free_slot_left) as e:
        logger.exception(e.message)
        raise HTTPError(500, "Internal error.")
    return {'session': sessionid}


@add_route('GET', '/logout')
def logout(http_context, config=None, sessions=None):
    headers = http_context['headers']
    logger.info("Removing session: %s" % (headers['X-Session']))
    try:
        username = check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.exception(e.message)
        logger.info("Invalid session.")
        raise e

    try:
        NotificationMgmt.push(config, Notification(
                                        username=username,
                                        message="Logout"))
    except NotificationError as e:
        logger.exception(e.message)

    try:
        sessions.delete(headers['X-Session'].encode('utf-8'))
    except (SharedItem_exists, SharedItem_no_free_slot_left) as e:
        logger.exception(e.message)
        raise HTTPError(500, "Internal error.")
    return {'logout': True}


@add_route('GET', '/discover')
def get_discover(http_context, config=None, sessions=None):
    conn = connector(
        host=config.postgresql['host'],
        port=config.postgresql['port'],
        user=config.postgresql['user'],
        password=config.postgresql['password'],
        database=config.postgresql['dbname']
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
            'plugins': [plugin_name for plugin_name in
                        config.temboard['plugins']]
        }
        conn.close()
        logger.info('Discovery done.')
        return ret

    except (error, Exception, HTTPError) as e:
        logger.exception(str(e))
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
def profile(http_context, config=None, sessions=None):
    headers = http_context['headers']
    logger.info("Get user profile.")
    try:
        check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.exception(e.message)
        logger.info("Invalid session.")
        raise e
    try:
        session = sessions.get_by_sessionid(
                    headers['X-Session'].encode('utf-8'))
        logger.info("Done.")
        return {'username': session.username}
    except SharedItem_not_found as e:
        logger.exception(e.message)
        logger.info("Failed.")
        raise HTTPError(401, "Invalid session.")


@add_route('GET', '/notifications')
def notifications(http_context, config=None, sessions=None):
    headers = http_context['headers']
    logger.info("Get notifications.")
    try:
        check_sessionid(headers, sessions)
    except HTTPError as e:
        logger.exception(e.message)
        logger.info("Invalid session.")
        raise e

    try:
        notifications = NotificationMgmt.get_last_n(config, -1)
        logger.info("Done.")
        return list(notifications)
    except (NotificationError, Exception) as e:
        logger.exception(e.message)
        logger.info("Failed.")
        raise HTTPError(500, "Internal error.")
