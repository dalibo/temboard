from flask import current_app as app
from flask import g, render_template, request

from ...model import orm
from ...version import inspect_versions


@app.route("/home")
def home():
    role = g.current_user
    environments = [
        e.name for e in role.select_environments().with_session(g.db_session).all()
    ]
    return render_template("home.html", environments=environments)


@app.route("/about")
def about():
    versions_info = inspect_versions()
    instances = g.db_session.scalar(orm.Instance.count())
    roles = g.db_session.scalar(orm.Role.count())
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
