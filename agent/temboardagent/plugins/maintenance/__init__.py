from datetime import datetime

from bottle import Bottle, default_app, request

from temboardagent.toolkit import taskmanager
from temboardagent.tools import validate_parameters

from . import functions


bottle = Bottle()
workers = taskmanager.WorkerSet()


@bottle.get('/')
def get_instance(pgconn, pgpool):
    instance = next(functions.get_instance(pgconn))

    rows = functions.get_databases(pgconn)

    databases = []
    for database in rows:
        database = dict(database)
        # we need to connect with a different database
        dbname = database['datname']
        dbconn = pgpool.getconn(dbname)
        database.update(**functions.get_database(dbconn))
        databases.append(database)

    return {'instance': instance, 'databases': databases}


T_VACUUM_MODE = b'(((^|,)(full|freeze|analyze))+$)'
T_TIMESTAMP_UTC = b'(^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$)'


@bottle.get('/<dbname>')
def get_database(pgpool, dbname):
    conn = pgpool.getconn(dbname)
    database = functions.get_database_size(conn)
    schemas = functions.get_schemas(conn)
    return dict(database, **{'schemas': schemas})


@bottle.get('/<dbname>/schema/<schema>')
def get_schema(pgpool, dbname, schema):
    conn = pgpool.getconn(dbname)
    tables = functions.get_tables(conn, schema)
    indexes = functions.get_schema_indexes(conn, schema)
    schema = functions.get_schema(conn, schema)
    return dict(dict(tables, **indexes), **schema)


@bottle.get('/<dbname>/schema/<schema>/table/<table>')
def get_table(pgpool, dbname, schema, table):
    conn = pgpool.getconn(dbname)
    ret = functions.get_table(conn, schema, table)
    ret.update(**functions.get_table_indexes(conn, schema, table))
    return ret


@bottle.post('/<dbname>/vacuum')
def post_vacuum_database(pgpool, dbname):
    return post_vacuum(pgpool, request.json, dbname)


@bottle.post('/<dbname>/schema/<schema>/table/<table>/vacuum')
def post_vacuum_table(pgpool, dbname, schema, table):
    return post_vacuum(pgpool, request.json, dbname, schema, table)


def post_vacuum(pgpool, post, dbname, schema=None, table=None):
    app = default_app().temboard
    # Parameters format validation
    if 'datetime' in post:
        validate_parameters(post, [
            ('datetime', T_TIMESTAMP_UTC, False),
        ])
    dt = post.get('datetime', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
    if 'mode' in post:
        validate_parameters(post, [
            ('mode', T_VACUUM_MODE, False),
        ])
    mode = post.get('mode', '')

    return functions.schedule_vacuum(
        pgpool.getconn(dbname), dbname, mode, dt, app, schema, table)


@bottle.get('/<dbname>/vacuum/scheduled')
def scheduled_vacuum_database(dbname):
    app = default_app().temboard
    return functions.list_scheduled_vacuum(app, dbname=dbname)


@bottle.get('/<dbname>/schema/<schema>/table/<table>/vacuum/scheduled')
def scheduled_vacuum_table(dbname, schema, table):
    app = default_app().temboard
    return functions.list_scheduled_vacuum(app, dbname=dbname, schema=schema,
                                           table=table)


@bottle.delete('/vacuum/<vacuum_id>')
def delete_vacuum(vacuum_id):
    app = default_app().temboard
    return functions.cancel_scheduled_operation(vacuum_id, app)


@bottle.get('/vacuum/scheduled')
def scheduled_vacuum():
    return functions.list_scheduled_vacuum(default_app().temboard)


@workers.register(pool_size=10)
def vacuum_worker(app, dbname, mode, schema=None, table=None):
    with app.postgres.connect(database=dbname) as conn:
        return functions.vacuum(conn, dbname, mode, schema, table)


@bottle.post('/<dbname>/analyze')
def post_analyze_database(pgpool, dbname):
    return post_analyze(pgpool, request.json, dbname)


@bottle.post('/<dbname>/schema/<schema>/table/<table>/analyze')
def post_analyze_table(pgpool, dbname, schema, table):
    return post_analyze(pgpool, request.json, dbname, schema, table)


def post_analyze(pgpool, post, dbname, schema=None, table=None):
    app = default_app().temboard
    # Parameters format validation
    if 'datetime' in post:
        validate_parameters(post, [
            ('datetime', T_TIMESTAMP_UTC, False),
        ])
    dt = post.get('datetime', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

    conn = pgpool.getconn(dbname)
    return functions.schedule_analyze(conn, dbname, dt, app, schema, table)


@bottle.get('/<dbname>/analyze/scheduled')
def scheduled_analyze_database(dbname):
    app = default_app().temboard
    return functions.list_scheduled_analyze(app, dbname=dbname)


@bottle.get('/<dbname>/schema/<schema>/table/<table>/analyze/scheduled')
def scheduled_analyze_table(dbname, schema, table):
    app = default_app().temboard
    return functions.list_scheduled_analyze(app, dbname=dbname, schema=schema,
                                            table=table)


@bottle.delete('/analyze/<analyze_id>')
def delete_analyze(analyze_id):
    app = default_app().temboard
    return functions.cancel_scheduled_operation(analyze_id, app)


@bottle.get('/analyze/scheduled')
def scheduled_analyze():
    app = default_app().temboard
    return functions.list_scheduled_analyze(app)


@workers.register(pool_size=10)
def analyze_worker(app, dbname, schema=None, table=None):
    with app.postgres.connect(database=dbname) as conn:
        return functions.analyze(conn, dbname, schema, table)


@bottle.post('/<dbname>/reindex')
def post_reindex_database(pgpool, dbname):
    return post_reindex(pgpool, request.json, dbname)


@bottle.post('/<dbname>/schema/<schema>/table/<table>/reindex')
def post_reindex_table(pgpool, dbname, schema, table):
    return post_reindex(pgpool, request.json, dbname, schema, table)


@bottle.post('/<dbname>/schema/<schema>/index/<index>/reindex')
def post_reindex_index(pgpool, dbname, schema, index):
    return post_reindex(pgpool, request.json, dbname, schema, index=index)


def post_reindex(pgpool, post, dbname, schema=None, table=None, index=None):
    app = default_app().temboard
    # Parameters format validation
    if 'datetime' in post:
        validate_parameters(post, [
            ('datetime', T_TIMESTAMP_UTC, False),
        ])
    dt = post.get('datetime', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

    return functions.schedule_reindex(
        pgpool.getconn(dbname), dbname, dt, app, schema, table, index)


@bottle.get('/<dbname>/reindex/scheduled')
def scheduled_reindex_database(dbname):
    app = default_app().temboard
    return functions.list_scheduled_reindex(app, dbname=dbname)


@bottle.get('/<dbname>/schema/<schema>/table/<table>/reindex/scheduled')
def scheduled_reindex_table(dbname, schema, table):
    app = default_app().temboard
    return functions.list_scheduled_reindex(
        app, dbname=dbname, schema=schema, table=table)


@bottle.get('/<dbname>/schema/<schema>/reindex/scheduled')
def scheduled_reindex_index(dbname, schema):
    app = default_app().temboard
    return functions.list_scheduled_reindex(app, dbname=dbname, schema=schema)


@bottle.delete('/reindex/<reindex_id>')
def delete_reindex(reindex_id):
    app = default_app().temboard
    return functions.cancel_scheduled_operation(reindex_id, app)


@bottle.get('/reindex/scheduled')
def scheduled_reindex(http_context, app):
    return functions.list_scheduled_reindex(app)


@workers.register(pool_size=10)
def reindex_worker(app, dbname, schema=None, table=None, index=None):
    with app.postgres.connect(database=dbname) as conn:
        return functions.reindex(conn, dbname, schema, table, index)


class MaintenancePlugin:
    PG_MIN_VERSION = (90400, 9.4)

    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        default_app().mount('/maintenance', bottle)
        self.app.worker_pool.add(workers)

    def unload(self):
        self.app.worker_pool.remove(workers)
