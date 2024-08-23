from flask import current_app as app
from flask import g, jsonify, redirect

from ...model.orm import Instance
from ..flask import admin_required, anonymous_allowed


@app.route("/")
@anonymous_allowed
def index():
    if g.current_user:
        return redirect("/home")
    return redirect("/login")


@app.route("/json/instances/home")
def get_instance_home():
    """Data for InstanceCards.vue component."""
    return jsonify(
        [
            {k: getattr(row, k) for k in row.keys()}
            for row in g.db_session.execute(
                Instance.select_for_home(g.current_user.role_name)
            )
        ]
    )


@app.route("/json/plugins")
@admin_required
def get_plugins():
    """List plugins."""
    return jsonify(sorted(app.temboard.config.temboard.plugins))
