from flask import current_app as app
from flask import g, render_template, request

from ...application import get_instance_groups_by_role
from ...model.orm import Instances, Roles
from ...version import inspect_versions


@app.route("/home")
def home():
    role = g.current_user

    groups = get_instance_groups_by_role(g.db_session, role.role_name)
    groups = [group for group in groups]

    return render_template("home.html", groups=groups)


@app.route("/about")
def about():
    versions_info = inspect_versions()
    instances = g.db_session.scalar(Instances.count())
    roles = g.db_session.scalar(Roles.count())
    infos = {
        "Browser": request.headers.get("User-Agent", "Unknown"),
        "Version": "%(temboard)s (%(temboardbin)s)" % versions_info,
        "Uptime": app.start_time,
        "OS": "%(distname)s %(distversion)s" % versions_info,
        "Python": "%(python)s (%(pythonbin)s)" % versions_info,
        "cryptography": versions_info["cryptography"],
        "Tornado": versions_info["tornado"],
        "libpq": versions_info["libpq"],
        "psycopg2": versions_info["psycopg2"],
        "SQLAlchemy": versions_info["sqlalchemy"],
        "Instances": instances,
        "Users": roles,
        "SMTP": app.temboard.config.notifications.smtp_host is not None,
        "Twilio": app.temboard.config.notifications.twilio_account_sid is not None,
    }
    temboard_version = versions_info["temboard"]

    return render_template("about.html", infos=infos, temboard_version=temboard_version)
