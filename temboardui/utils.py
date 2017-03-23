import logging
from time import sleep

logger = logging.getLogger(__name__)


def check_sqlalchemy_connectivity(engine):
    for i in range(10):
        try:
            conn = engine.connect()
            conn.close()
            break
        except Exception as e:
            if i == 9:
                raise
            logger.warn("Failed to connect to database: %s", e)
            logger.info("Retrying in %ss.", i)
            sleep(i)
