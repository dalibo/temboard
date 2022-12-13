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
        "Browser": request.headers.get('User-Agent', 'Unknown'),
        "Version": "%(temboard)s (%(temboardbin)s)" % versions_info,
        "Uptime": app.start_time,
        "OS": "%(distname)s %(distversion)s" % versions_info,
        "Python": "%(python)s (%(pythonbin)s)" % versions_info,
        "cryptography": versions_info['cryptography'],
        "Tornado": versions_info['tornado'],
        "libpq": versions_info['libpq'],
        "psycopg2": versions_info['psycopg2'],
        "SQLAlchemy": versions_info['sqlalchemy'],
    }
    temboard_version = versions_info['temboard']

    return render_template(
        'about.html',
        nav=True,
        role=request.current_user,
        infos=infos,
        temboard_version=temboard_version
    )
