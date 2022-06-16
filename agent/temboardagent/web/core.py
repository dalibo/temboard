import logging
import time

from bottle import default_app, get, request

from ..routing import add_route
from ..errors import HTTPError
from ..notification import NotificationMgmt
from ..inventory import SysInfo, PgInfo
from ..toolkit.signing import canonicalize_request, verify_v1, InvalidSignature
from ..version import __version__ as version


logger = logging.getLogger(__name__)


@get('/discover', skip=['signature'])
def get_discover():
    logger.info('Starting discovery.')
    app = default_app().temboard
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

    signature = request.headers.get('x-temboard-signature')
    if signature:
        crequest = canonicalize_request(
            request.method,
            request.path,
            request.headers,
        )
        try:
            if not signature.startswith('v1:'):
                raise InvalidSignature("Unsupported signature version.")
            signature = signature[3:]

            verify_v1(
                app.config.signing_key, signature, crequest)
            sign_status = 'valid'
        except InvalidSignature:
            sign_status = 'invalid'
    else:
        sign_status = 'enabled'

    discover['signature_status'] = sign_status

    logger.info('Discovery done.')
    logger.debug(discover)
    return discover


@get
def profile():
    return {'username': request.username, 'signature': 'valid'}


@get('/notifications')
def notifications():
    config = default_app().temboard.config
    return list(NotificationMgmt.get_last_n(config, -1))


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
