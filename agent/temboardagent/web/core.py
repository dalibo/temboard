import logging

from bottle import default_app, get, post, request

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
        pg_port=app.config.postgresql['port'],
        pg_version=None,
        pg_version_summary=None,
        pg_data=None,
        plugins=app.config.temboard['plugins'],
        signature_status='enabled',
    )

    # Gather system informations
    sysinfo = SysInfo()
    discover.update(
        hostname=sysinfo.hostname(app.config.temboard['hostname']),
        cpu=sysinfo.n_cpu(),
        memory_size=sysinfo.memory_size(),
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
    except Exception:
        logger.exception('Postgres discovery failed.')
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
            discover['signature_status'] = 'valid'
        except InvalidSignature:
            discover['signature_status'] = 'invalid'

    return discover


@post('/discover')
def post_discover(pgconn):
    app = default_app().temboard
    data = app.discover.refresh(pgconn).copy()
    # POST endpoint does not bypass signature verification.
    data['signature_status'] = 'valid'
    response.set_header('ETag', app.discover.etag)
    return data


@get
def profile():
    return {'username': request.username, 'signature': 'valid'}


@get('/notifications')
def notifications():
    config = default_app().temboard.config
    return list(NotificationMgmt.get_last_n(config, -1))


@get('/status', skip=['signature'])
def get_status():
    app = default_app().temboard

    try:
        reload_datetime = app.reload_datetime.strftime("%Y-%m-%dT%H:%M:%S%Z")
    except AttributeError:
        reload_datetime = None

    return dict(
        pid=app.pid,
        user=app.user,
        start_datetime=app.start_datetime.strftime("%Y-%m-%dT%H:%M:%S%Z"),
        reload_datetime=reload_datetime,
        configfile=app.config.temboard.configfile,
        version=version,
    )
