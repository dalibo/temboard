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
from temboardagent.notification import NotificationMgmt, Notification
from temboardagent.inventory import SysInfo, PgInfo
from .version import __version__ as version


logger = logging.getLogger(__name__)


def check_sessionid(http_header, sessions):
    """
    Check X-Session is valid and the session exists.
    """
    validate_parameters(http_header,
                        [('X-Session', T_SESSIONID, False)])
    try:
        xsession = http_header['X-Session'].encode('utf-8')
        session = sessions.get_by_sessionid(xsession)
        session.time = time.time()
        username = session.username
        sessions.update(session)
        return username
    except SharedItem_not_found:
        raise HTTPError(401, "Invalid session.")


@add_route('POST', b'/login', check_session=False)
def login(http_context, app, sessions):
    post = http_context['post']
    # Add an unconditional sleeping time to reduce brute-force risks
    time.sleep(1)

    logger.info("Authenticating user: %s" % (post['username']))
    try:
        validate_parameters(post,
                            [('username', T_USERNAME, False),
                             ('password', T_PASSWORD, False)])
        auth_user(app.config.temboard['users'],
                  post['username'], post['password'])
    except HTTPError as e:
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
            NotificationMgmt.push(app.config,
                                  Notification(username=post['username'],
                                               message="Login"))
        except NotificationError as e:
            logger.exception(e)

        return {'session': sessionid}
    except (SharedItem_exists, SharedItem_no_free_slot_left) as e:
        logger.exception(e)
        raise HTTPError(500, "Internal error.")


@add_route('GET', b'/logout')
def logout(http_context, app, sessions):
    headers = http_context['headers']
    logger.info("Removing session: %s" % (headers['X-Session']))
    try:
        NotificationMgmt.push(app.config,
                              Notification(username=http_context['username'],
                                           message="Logout"))
    except NotificationError as e:
        logger.exception(e)

    try:
        sessions.delete(headers['X-Session'].encode('utf-8'))
        return {'logout': True}
    except (SharedItem_exists, SharedItem_no_free_slot_left) as e:
        logger.exception(e)
        raise HTTPError(500, "Internal error.")


@add_route('GET', b'/discover', check_session=False)
def get_discover(http_context, app, sessions):
    logger.info('Starting discovery.')

    discover = dict(
        hostname=None,
        cpu=None,
        memory_size=None,
        pg_port=app.config.postgresql['port'],
        pg_version=None,
        pg_version_summary=None,
        pg_data=None,
        plugins=[plugin for plugin in app.config.temboard['plugins']],
    )

    try:
        # Gather system informations
        sysinfo = SysInfo()
        hostname = sysinfo.hostname(app.config.temboard['hostname'])
        cpu = sysinfo.n_cpu()
        memory_size = sysinfo.memory_size()

    except (Exception, HTTPError) as e:
        logger.exception(str(e))
        logger.error('System discovery failed.')
        # We stop here if system information has not been collected
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")

    discover.update(
        hostname=hostname, cpu=cpu, memory_size=memory_size
    )

    try:
        with app.postgres.connect() as conn:
            pginfo = PgInfo(conn)
            discover.update(
                pg_block_size=int(pginfo.setting('block_size')),
                pg_version=pginfo.version()['full'],
                pg_version_summary=pginfo.version()['summary'],
                pg_data=pginfo.setting('data_directory')
            )

    except Exception as e:
        logger.exception(str(e))
        logger.error('Postgres discovery failed.')
        # Do not raise HTTPError, just keeping null values for Postgres
        # informations.

    logger.info('Discovery done.')
    logger.debug(discover)
    return discover


@add_route('GET', b'/profile')
def profile(http_context, app, sessions):
    headers = http_context['headers']
    logger.info("Get user profile.")
    try:
        xsession = headers['X-Session'].encode('utf-8')
        session = sessions.get_by_sessionid(xsession)
        logger.info("Done.")
        return {'username': session.username.decode('utf-8')}
    except SharedItem_not_found as e:
        logger.exception(e)
        logger.info("Failed.")
        raise HTTPError(401, "Invalid session.")


@add_route('GET', b'/notifications', check_key=True)
def notifications(http_context, app, sessions):
    logger.info("Get notifications.")
    try:
        notifications = NotificationMgmt.get_last_n(app.config, -1)
        logger.info("Done.")
        return list(notifications)
    except (NotificationError, Exception) as e:
        logger.exception(e)
        logger.info("Failed.")
        raise HTTPError(500, "Internal error.")


@add_route('GET', b'/status', check_session=False)
def get_status(http_context, app, sessions):
    logger.info('Starting /status.')
    try:
        start_datetime = time.strftime("%Y-%m-%dT%H:%M:%S%Z",
                                       app.start_datetime.timetuple())
        reload_datetime = time.strftime("%Y-%m-%dT%H:%M:%S%Z",
                                        app.start_datetime.timetuple())
        ret = dict(
            pid=app.pid,
            user=app.user,
            start_datetime=start_datetime,
            reload_datetime=reload_datetime,
            configfile=app.config.temboard.configfile,
            version=version,
        )
        logger.info('Ending /status.')
        return ret
    except (Exception, HTTPError) as e:
        logger.exception(str(e))
        logger.info('Status failed.')
        if isinstance(e, HTTPError):
            raise e
        else:
            raise HTTPError(500, "Internal error.")
