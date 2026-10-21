from dateutil import parser as parse_datetime
from flask import abort, g, request

from ..model import db


def get_request_ids():
    host_id = db.get_host_id(g.db_session, g.instance.hostname)
    instance_id = db.get_instance_id(g.db_session, host_id, g.instance.pg_port)
    return host_id, instance_id


def parse_start_end():
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        if start:
            start = parse_datetime.parse(start)
        if end:
            end = parse_datetime.parse(end)
    except ValueError:
        abort(406, "Datetime not valid.")

    return start, end
