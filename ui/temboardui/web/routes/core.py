from flask import current_app as app
from flask import g, jsonify, redirect

from ...model.orm import Instances
from ..flask import anonymous_allowed


@app.route("/")
@anonymous_allowed
def index():
    return redirect("/home")


@app.route("/json/instances/home")
def get_instance_home():
    """Data for InstanceCards.vue component."""
    return jsonify(
        [
            {k: getattr(row, k) for k in row.keys()}
            for row in g.db_session.execute(
                Instances.select_for_home(g.current_user.role_name)
            )
        ]
    )
