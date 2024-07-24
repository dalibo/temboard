import logging

from flask import current_app as app
from flask import g, render_template

from ..flask import instance_routes

logger = logging.getLogger(__name__)


@instance_routes.route("/about")
def instance_about():
    app.instance.fetch_status()
    return render_template(
        "instance-about.html",
        instance_name=g.instance.__str__(),
        pg_data=g.instance.pg_data,
        pg_version_summary=g.instance.pg_version_summary,
        discover=g.instance.discover,
        environment=g.instance.environment.name,
    )


@app.route("/explain")
def explain():
    return render_template(
        "explain.html", nav=True, role=g.current_user, vitejs=app.vitejs
    )
