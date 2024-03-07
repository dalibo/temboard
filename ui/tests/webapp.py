#
# Simple web app based on temboardui.web API.
#
# Run it with libpq env vars.
#
#    PGHOST=0.0.0.0 PGUSER=temboard PGPASSWORD=temboard tests/webapp.py
#
# See below available routes.

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from tornado.ioloop import IOLoop
from tornado.web import HTTPError

from temboardui.web import (
    Redirect,
    Response,
    app,
    render_template,
)
from temboardui.application import (
    gen_cookie,
    hash_password,
)
from temboardui.model import configure as configure_db_session


logger = logging.getLogger(__name__)


# Simple test app: Run it with python -m temboardui.web.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)5.5s %(message)s",
)

app.configure(
    debug=True,
    cookie_secret='confidentiel',
)
app.executor = ThreadPoolExecutor(4)
# Just use libpq settings.
dsn = 'postgresql://%(PGHOST)s' % os.environ
configure_db_session(dsn=dsn)


@app.route(r'/')
def index(request):
    return u'OK\n'


@app.route(r'/sleep/(\d+)')
def sleep_(request, seconds):
    sleep(int(seconds))
    return u'%s\n' % seconds


@app.route(r'/post', methods=['POST'])
def post(request):
    return u'%r\n' % request.body_arguments


@app.route(r'/template/(.+\.html)')
def html(request, template):
    return render_template(template, var='toto')


@app.route(r'/redirect')
def redirect(request):
    return Redirect(location='/', permanent=True)


@app.route(r'/login/([^/]+)')
def login(request, username):
    password = hash_password(username, username)
    cookie = gen_cookie(username, hash_password=password)
    return Response(secure_cookies={'temboard': cookie})


@app.route(r'/whoami')
def whoami(request):
    # This request handlers checks cookie and db access.
    try:
        return request.current_user.role_name
    except AttributeError:
        raise HTTPError(404)


if '__main__' == __name__:
    logger.debug("Serving on http://0.0.0.0:9000/.")

    app.listen(9000)
    IOLoop.current().start()
