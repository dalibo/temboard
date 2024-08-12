from flask import current_app as app
from flask import g, render_template

from ...model import orm
from ..flask import admin_required


@app.route("/settings/instances")
@admin_required
def get_instances():
    return render_template(
        "settings/instances.html",
        nav=True,
        vitejs=app.vitejs,
        role=g.current_user,
        instance_list=orm.Instances.all().with_session(g.db_session).all(),
    )


@app.route("/settings/users")
@admin_required
def get_users():
    return render_template(
        "settings/users.html",
        nav=True,
        vitejs=app.vitejs,
        role=g.current_user,
        role_list=orm.Roles.all().with_session(g.db_session).all(),
    )
