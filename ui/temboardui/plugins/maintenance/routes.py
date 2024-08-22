from flask import current_app, render_template

from ...web.flask import instance_routes

PLUGIN_NAME = "maintenance"


@instance_routes.route("/maintenance")
def maintenance():
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template("maintenance/index.html", plugin=PLUGIN_NAME)


@instance_routes.route("/maintenance/<database>/schema/<schema>/table/<table>")
def table(database, schema, table):
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/table.html",
        plugin=PLUGIN_NAME,
        database=database,
        schema=schema,
        table=table,
    )


@instance_routes.route("/maintenance/<database>/schema/<schema>")
def schema(database, schema):
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/schema.html", plugin=PLUGIN_NAME, database=database, schema=schema
    )


@instance_routes.route("/maintenance/<database>")
def database(database):
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/database.html", plugin=PLUGIN_NAME, database=database
    )
