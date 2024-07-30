import codecs
from io import StringIO

from temboardui.web.tornado import Response, admin_required, app

from ...model import QUERIES


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
