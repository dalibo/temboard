import logging

import psycopg2
from bottle import HTTPError, default_app, request

from ...tools import validate_parameters
from ...web.app import CustomBottle

bottle = CustomBottle()
logger = logging.getLogger(__name__)


@bottle.post("/")
def post_explain(pgconn):
    validate_parameters(request.json, [("query", str, True), ("options", str, True)])
    query = request.json["query"]
    options = request.json["options"] + ["FORMAT JSON"]
    try:
        r = pgconn.queryone(f"EXPLAIN ({', '.join(options)}) {query}")
    except psycopg2.errors.DatabaseError as e:
        return HTTPError(400, e.pgerror)
    return r["QUERY PLAN"]


class ExplainPlugin:
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        default_app().mount("/explain", bottle)
