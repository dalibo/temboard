import logging

from temboardui.web.tornado import (
    HTTPError,
    csvify,
)

from . import blueprint, render_template
from ..chartdata import (
    get_unavailability_csv,
    get_metric_data_csv,
)
from ..tools import (
    get_request_ids,
    parse_start_end,
)

logger = logging.getLogger(__name__)


@blueprint.instance_route("/monitoring")
def index(request):
    request.instance.check_active_plugin('monitoring')
    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        # Monitoring plugin doesn't require agent authentication since we
        # already have the data.
        # Don't fail if there's a session error (for example when the agent
        # has been restarted)
        agent_username = None

    return render_template(
        'index.html',
        nav=True, role=request.current_user, instance=request.instance,
        plugin='monitoring', agent_username=agent_username,
    )


@blueprint.instance_route("/monitoring/unavailability")
def unavailability(request):
    try:
        host_id, instance_id = get_request_ids(request)
    except NameError as e:
        logger.info("%s. No data.", e)
        return csvify(data=[])

    start, end = parse_start_end(request)
    data = get_unavailability_csv(
        request.db_session, start, end, host_id, instance_id)
    return csvify(data)


@blueprint.instance_route(r'/monitoring/data/([a-z\-_.0-9]{1,64})$')
def data_metric(request, metric_name):
    key = request.handler.get_argument('key', default=None)
    try:
        host_id, instance_id = get_request_ids(request)
    except NameError as e:
        logger.info("%s. No data.", e)
        return csvify(data=[])

    start, end = parse_start_end(request)
    try:
        data = get_metric_data_csv(
            request.db_session, metric_name,
            start, end,
            host_id=host_id,
            instance_id=instance_id,
            key=key,
        )
    except IndexError:
        raise HTTPError(404, 'Unknown metric.')

    return csvify(data=data)
