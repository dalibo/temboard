from flask import g

from ..model import db


def get_request_ids():
    host_id = db.get_host_id(g.db_session, g.instance.hostname)
    instance_id = db.get_instance_id(g.db_session, host_id, g.instance.pg_port)
    return host_id, instance_id
