import codecs
import logging
from io import StringIO

from temboardui.application import delete_instance
from temboardui.web.tornado import HTTPError, Response, admin_required, app

from ...model import QUERIES

logger = logging.getLogger(__name__)


@app.route(r"/json/settings/delete/instance$", methods=["POST"])
@admin_required
def json_delete_instance(request):
    data = request.json
    if not data.get("agent_address"):
        raise HTTPError(400, "Agent address field is missing.")
    if not data.get("agent_port"):
        raise HTTPError(400, "Agent port field is missing.")
    delete_instance(request.db_session, **data)
    return {"delete": True}


@app.route(r"/settings/instances.csv")
@admin_required
def instances_csv(request):
    search = request.handler.get_query_argument("filter")
    search = "%%%s%%" % search if search else "%"
    bind = request.db_session.get_bind()
    conn = bind.raw_connection().connection
    sql = QUERIES["copy-instances-as-csv"]
    with conn.cursor() as cur, StringIO() as fo:
        sql = cur.mogrify(sql, (search,))
        cur.copy_expert(sql, fo)
        csv = fo.getvalue()

    filename = "postgresql-instances-inventory.csv"
    return Response(
        status_code=200,
        headers={
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment;filename=" + filename,
        },
        # BOM declares UTF8 for Excell.
        body=codecs.BOM_UTF8 + csv.encode("utf-8"),
    )
