from flask import current_app, render_template

from ...web.flask import instance_routes


@instance_routes.route("/pgconf/configuration", methods=["GET"])
def pgconf_configuration():
    current_app.instance.check_active_plugin("pgconf")
    current_app.instance.fetch_status()

    return render_template("configuration.html", plugin="pgconf")
