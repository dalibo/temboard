from ..application import (
    get_instance_groups_by_role,
)
from ..version import inspect_versions
from ..web.tornado import (
    app,
    render_template,
)


@app.route('/home')
def home(request):
    role = request.current_user

    groups = get_instance_groups_by_role(request.db_session, role.role_name)
    groups = [group for group in groups]

    return render_template(
        'home.html',
        nav=True, role=role,
        groups=groups,
    )


@app.route("/about")
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
        'about.html',
        nav=True,
        role=request.current_user,
        infos=infos,
        temboard_version=temboard_version
    )
