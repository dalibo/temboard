from flask import current_app as app
from flask import g, render_template

from ...model import orm
from ..flask import admin_required


@app.route("/settings/instances")
@admin_required
def settings_instances():
    return render_template(
        "settings/instances.html",
        sidebar=True,
        instance_list=orm.Instance.all().with_session(g.db_session).all(),
    )


@app.route("/settings/environments")
@admin_required
def settings_environments():
    return render_template(
        "settings/environments.html",
        sidebar=True,
        environments=orm.Environment.all().with_session(g.db_session).all(),
    )


@app.route("/settings/environments/<name>/members")
@admin_required
def settings_environment_members(name):
    return render_template("settings/members.html", sidebar=True, environment=name)


@app.route("/settings/users")
@admin_required
def settings_users():
    return render_template(
        "settings/users.html",
        sidebar=True,
        role_list=orm.Role.all().with_session(g.db_session).all(),
    )
