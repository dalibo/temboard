from ..application import get_instance_groups_by_role
from ..model.orm import Instances, Roles
from ..version import inspect_versions
from ..web.tornado import app, render_template


@app.route("/home")
def home(request):
    role = request.current_user

    groups = get_instance_groups_by_role(request.db_session, role.role_name)
    groups = [group for group in groups]

    return render_template("home.html", nav=True, role=role, groups=groups)


@app.route("/about")
def about(request):
    versions_info = inspect_versions(prometheusbin=request.config.monitoring.prometheus)
    instances = request.db_session.scalar(Instances.count())
    roles = request.db_session.scalar(Roles.count())
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
        "Prometheus": "%(prometheus)s (%(prometheusbin)s)" % versions_info,
        "SQLAlchemy": versions_info["sqlalchemy"],
        "Instances": instances,
        "Users": roles,
        "SMTP": request.config.notifications.smtp_host is not None,
        "Twilio": request.config.notifications.twilio_account_sid is not None,
    }
    temboard_version = versions_info["temboard"]

    return render_template(
        "about.html",
        nav=True,
        role=request.current_user,
        infos=infos,
        temboard_version=temboard_version,
    )
