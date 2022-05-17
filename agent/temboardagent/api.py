import logging
import time

from temboardagent.routing import add_route
from temboardagent.errors import (
    HTTPError,
    NotificationError,
)
from temboardagent.notification import NotificationMgmt
from temboardagent.inventory import SysInfo, PgInfo
from .version import __version__ as version


logger = logging.getLogger(__name__)


@add_route('GET', b'/discover', public=True)
def get_discover(http_context, app):
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
def profile(http_context, app):
    logger.info("Get user profile.")
    return {'username': http_context['username']}


@add_route('GET', b'/notifications')
def notifications(http_context, app):
    logger.info("Get notifications.")
    try:
        notifications = NotificationMgmt.get_last_n(app.config, -1)
        logger.info("Done.")
        return list(notifications)
    except (NotificationError, Exception) as e:
        logger.exception(e)
        logger.info("Failed.")
        raise HTTPError(500, "Internal error.")


@add_route('GET', b'/status', public=True)
def get_status(http_context, app):
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
