import logging

from temboardui.web.tornado import admin_required, app, render_template

from ...version import inspect_versions

logger = logging.getLogger(__name__)


@app.route(r"/settings/metadata")
@admin_required
def metadata(request):

    versions_info = inspect_versions()
    infos = {
        "Version": "%(temboard)s (%(temboardbin)s)" % versions_info,
        "Uptime": app.start_time,
        "OS": "%(distname)s %(distversion)s" % versions_info,
        "Python": "%(python)s (%(pythonbin)s)" % versions_info,
        "cryptography": "%(cryptography)s" % versions_info,
        "Tornado": "%(tornado)s" % versions_info,
        "libpq": "%(libpq)s" % versions_info,
        "psycopg2": "%(psycopg2)s" % versions_info,
        "SQLAlchemy": "%(sqlalchemy)s" % versions_info,
    }
    temboard_version = "%(temboard)s" % versions_info

    return render_template(
        'settings/metadata.html',
        nav=True,
        role=request.current_user,
        infos=infos,
        temboard_version=temboard_version
    )
