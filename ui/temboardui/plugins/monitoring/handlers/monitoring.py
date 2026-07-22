import logging


from ..chartdata import get_metric_data_csv, get_unavailability_csv
from ..tools import get_request_ids, parse_start_end
from flask import abort, current_app, g, render_template, request
from ....web.flask import csvify, instance_routes

logger = logging.getLogger(__name__)


@instance_routes.route("/monitoring")
def index():
    current_app.instance.check_active_plugin("monitoring")
    current_app.instance.fetch_status()
    return render_template(
        "monitoring/index.html",
        role=g.current_user,
        instance=g.instance,
        plugin="monitoring",
        vitejs=current_app.vitejs,
    )


@instance_routes.route("/monitoring/unavailability")
def unavailability():
    try:
        host_id, instance_id = get_request_ids()
    except NameError as e:
        logger.info("%s. No data.", e)
        return csvify(data=[])

    start, end = parse_start_end()
    data = get_unavailability_csv(g.db_session, start, end, host_id, instance_id)
    return csvify(data)


@instance_routes.route(r"/monitoring/data/<metric_name>")
def data_metric(metric_name):
    key = request.args.get("key")
    try:
        host_id, instance_id = get_request_ids()
    except NameError as e:
        logger.info("%s. No data.", e)
        return csvify(data=[])

    start, end = parse_start_end()
    try:
        data = get_metric_data_csv(
            g.db_session,
            metric_name,
            start,
            end,
            host_id=host_id,
            instance_id=instance_id,
            key=key,
        )
    except IndexError:
        raise abort(400, "Unknown metric.")

    return csvify(data=data)
