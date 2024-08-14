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
        vitejs=app.vitejs,
        role=g.current_user,
        instance_list=orm.Instances.all().with_session(g.db_session).all(),
    )


@app.route("/settings/groups/instance")
@admin_required
def settings_instance_groups():
    return render_template(
        "settings/instance-groups.html",
        sidebar=True,
        vitejs=app.vitejs,
        role=g.current_user,
        groups=orm.Groups.all("instance").with_session(g.db_session).all(),
    )


@app.route("/settings/users")
@admin_required
def settings_users():
    return render_template(
        "settings/users.html",
        sidebar=True,
        vitejs=app.vitejs,
        role=g.current_user,
        role_list=orm.Roles.all().with_session(g.db_session).all(),
    )


@app.route("/settings/groups/role")
@admin_required
def settings_groups():
    return render_template(
        "settings/groups.html",
        sidebar=True,
        role=g.current_user,
        vitejs=app.vitejs,
        groups=orm.Groups.all("role").with_session(g.db_session).all(),
    )
