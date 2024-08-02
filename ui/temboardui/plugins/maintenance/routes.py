from flask import current_app, g, render_template

from ...web.flask import instance_routes

PLUGIN_NAME = "maintenance"


@instance_routes.route("/maintenance")
def maintenance():
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/index.html",
        nav=True,
        instance=g.instance,
        plugin=PLUGIN_NAME,
        role=g.current_user,
        vitejs=current_app.vitejs,
    )


@instance_routes.route("/maintenance/<database>/schema/<schema>/table/<table>")
def table(database, schema, table):
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/table.html",
        nav=True,
        instance=g.instance,
        plugin=PLUGIN_NAME,
        role=g.current_user,
        database=database,
        schema=schema,
        table=table,
        vitejs=current_app.vitejs,
    )


@instance_routes.route("/maintenance/<database>/schema/<schema>")
def schema(database, schema):
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/schema.html",
        nav=True,
        instance=g.instance,
        plugin=PLUGIN_NAME,
        role=g.current_user,
        database=database,
        schema=schema,
        vitejs=current_app.vitejs,
    )


@instance_routes.route("/maintenance/<database>")
def database(database):
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "maintenance/database.html",
        nav=True,
        instance=g.instance,
        plugin=PLUGIN_NAME,
        role=g.current_user,
        database=database,
        vitejs=current_app.vitejs,
    )
