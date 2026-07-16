import json
import logging

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import case, column, extract, func
from temboardtoolkit import taskmanager

from temboardui.agentclient import TemboardAgentClient
from temboardui.model import worker_engine
from temboardui.model.orm import Instance

logger = logging.getLogger(__name__)
workers = taskmanager.WorkerSet()


class StatementsPlugin:
    def __init__(self, app):
        self.app = app

    def load(self):
        __import__(__name__ + ".routes")
        self.app.worker_pool.add(workers)
        self.app.scheduler.add(workers)


def add_statement(session, instance, data):
    agent_id = f"{instance.agent_address}:{instance.agent_port}"
    if not data.get("data"):
        logger.info("No statement data from %s.", agent_id)
        return

    conn = session.connection().connection
    cur = conn.cursor()
    cur.execute("SET search_path TO statements")
    for statement in data.get("data"):
        query = """
            INSERT INTO statements_src_tmp
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            query,
            (
                instance.agent_address,
                instance.agent_port,
                data["snapshot_datetime"],
                statement["userid"],
                statement["rolname"],
                statement["dbid"],
                statement["datname"],
                statement["queryid"],
                statement["query"],
                statement["calls"],
                statement["total_exec_time"]
                if "total_exec_time" in statement
                else statement["total_time"],
                statement["rows"],
                statement["shared_blks_hit"],
                statement["shared_blks_read"],
                statement["shared_blks_dirtied"],
                statement["shared_blks_written"],
                statement["local_blks_hit"],
                statement["local_blks_read"],
                statement["local_blks_dirtied"],
                statement["local_blks_written"],
                statement["temp_blks_read"],
                statement["temp_blks_written"],
                # DEPRECATED: Column renamed in Postgres 17.
                statement["shared_blk_read_time"]
                if "shared_blk_read_time" in statement
                else statement["blk_read_time"],
                statement["shared_blk_write_time"]
                # DEPRECATED: Column renamed in Postgres 17.
                if "shared_blk_write_time" in statement
                else statement["blk_write_time"],
                statement["total_plan_time"]
                if "total_plan_time" in statement
                else None,
                statement["wal_records"] if "wal_records" in statement else None,
                statement["wal_fpi"] if "wal_fpi" in statement else None,
                statement["wal_bytes"] if "wal_bytes" in statement else None,
            ),
        )
    query = """SELECT process_statements(%s, %s)"""
    cur.execute(query, (instance.agent_address, instance.agent_port))
    conn.commit()


@workers.schedule(id="statements_pull_data", redo_interval=60)  # 1m
@workers.register(pool_size=1)
def pull_data_worker(app):
    engine = worker_engine(app.config.repository)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    worker_session = Session()
    instances = worker_session.query(Instance)

    if not instances:
        logger.info("No instances to pull data from.")
        return

    for instance in instances:
        plugin_names = [plugin.plugin_name for plugin in instance.plugins]

        if "statements" not in plugin_names:
            logger.debug("Skipping instance %s. Plugin disabled.", instance)
            continue

        # FIXME should be done in parallel
        try:
            pull_data_for_instance(app, worker_session, instance)
        except Exception:
            logger.exception(
                "Failed to pull data from %s:%s",
                instance.agent_address,
                instance.agent_port,
            )


@workers.register(pool_size=1)
def statements_pull1(app, host, port):
    engine = worker_engine(app.config.repository)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    worker_session = Session()
    instance = Instance.get(host, port).with_session(worker_session).first()

    try:
        pull_data_for_instance(app, worker_session, instance)
    except Exception:
        logger.exception(
            "Failed to pull data from %s:%s",
            instance.agent_address,
            instance.agent_port,
        )


def pull_data_for_instance(app, session, instance):
    agent_id = f"{instance.agent_address}:{instance.agent_port}"
    logger.info("Pulling statements from %s.", agent_id)
    client = TemboardAgentClient.factory(
        app.config, instance.agent_address, instance.agent_port
    )
    try:
        response = client.get("/statements")
        response.raise_for_status()
        add_statement(session, instance, response.json())
        logger.debug("Successfully pulled statements data for %s.", agent_id)
    except Exception as e:
        error = "Error while fetching statements from instance: "
        if hasattr(e, "read"):
            error += json.loads(e.read())["error"]
        else:
            error += str(e)

        if isinstance(e, (OSError, ConnectionError, client.Error)):
            logger.error(
                "Failed to query agent: %s. Is it running? agent=%s", error, agent_id
            )
        else:
            logger.exception("Failed to pull statements data: %s", error)

        # If statements data cannot be retrieved store the error in the
        # statements metas table
        cur = session.connection().connection.cursor()
        cur.execute("SET search_path TO statements")
        query = """
            -- Create new meta for agent if doesn't already exist
            INSERT INTO metas (agent_address, agent_port)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """
        cur.execute(query, (instance.agent_address, instance.agent_port))

        query = """
            UPDATE metas
            SET error = %s
            WHERE agent_address = %s AND agent_port = %s;
        """
        cur.execute(query, (error, instance.agent_address, instance.agent_port))
        session.connection().connection.commit()


@workers.schedule(id="statements_purge", redo_interval=24 * 60 * 60)  # 24h
@workers.register(pool_size=1)
def statements_purge_worker(app):
    """Background worker in charge of purging statements data.
    Purge policy is based on purge_after parameter from statements section.
    purge_after sets the number of days of data to keep, from now. Default is
    7 days if not set.
    """
    logger.info("Purging old data.")

    engine = worker_engine(app.config.repository)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    session = Session()

    purge_after = app.config.statements.purge_after

    # Get tablename list to purge from metric_tables_config()
    try:
        cur = session.connection().connection.cursor()
        cur.execute("SET search_path TO statements")
        cur.execute("""SELECT statements_purge(%s)""", (purge_after,))
        session.connection().connection.commit()
        logger.debug("Old statements purged successfully.")
    except Exception:
        logger.exception("Could not purge statements data:")
        raise


def to_epoch(column):
    return extract("epoch", column).label(column.name)


def diff(var):
    return (func.max(column(var)) - func.min(column(var))).label(var)


def total_measure_interval(column):
    return extract(
        "epoch",
        case([(func.min(column) == "0 second", "1 second")], else_=func.min(column)),
    )


# We use 8192 as default value for block size
# Ideally we should get this value from agent
block_size = 8192


def total_read(c):
    return (
        func.sum(c.shared_blks_read + c.local_blks_read + c.temp_blks_read)
        / total_measure_interval(c.mesure_interval)
    ).label("total_blks_read")


def total_hit(c):
    return (
        func.sum(c.shared_blks_hit + c.local_blks_hit)
        / total_measure_interval(c.mesure_interval)
    ).label("total_blks_hit")


class Biggest:
    def __init__(self, order_by):
        self.order_by = order_by

    def __call__(self, var, minval=0, label=None):
        label = label or var
        return func.greatest(
            column(var) - func.lag(column(var)).over(order_by=self.order_by), minval
        ).label(label)


class Biggestsum:
    def __init__(self, order_by):
        self.order_by = order_by

    def __call__(self, var, minval=0, label=None):
        label = label or var
        return func.greatest(
            func.sum(column(var))
            - func.lag(func.sum(column(var))).over(order_by=self.order_by),
            minval,
        ).label(label)
