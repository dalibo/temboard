import logging

from .agentclient import TemboardAgentClient
from .model import worker_engine, Session
from .model.orm import Instances
from .toolkit.taskmanager import WorkerSet
from .toolkit.utils import utcnow


logger = logging.getLogger(__name__)
workers = WorkerSet()


@workers.register(pool_size=1)
def refresh_discover(app, address, port):
    session = Session(bind=worker_engine(app.config.repository))
    instance = Instances.get(address, port).with_session(session).one()
    client = TemboardAgentClient.factory(app.config, address, port)
    try:
        logger.info("Discovering %s.", instance)
        response = client.get('/discover')
        response.raise_for_status()
    except (OSError, client.ConnectionError, client.Error) as e:
        logger.error("Failed to discover %s: %s", instance, e)
        logger.error("Agent or host may be down or misconfigured.")
        return

    discover_etag = response.headers.get('ETag')
    if discover_etag == instance.discover_etag:
        logger.info("Discover data up to date for %s.", instance)
        return

    instance.discover = response.json()
    instance.discover_etag = discover_etag
    instance.discover_date = utcnow()
    session.commit()

    logger.info("Updated discover data for %s.", instance)
