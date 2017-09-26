from distutils.util import strtobool
import logging
import os
import pdb
import sys

from .cli import main
from .errors import UserError
from .logger import LOG_FORMAT


logger = logging.getLogger('temboardagent')
debug = strtobool(os.environ.get('DEBUG', '0'))

retcode = 1
try:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format=LOG_FORMAT,
    )
    logger.debug("Starting temBoard agent.")
    retcode = main()
except pdb.bdb.BdbQuit:
    logger.info("Graceful exit from debugger.")
except UserError as e:
    retcode = e.retcode
    logger.critical("FATAL: %s", e)
except Exception as e:
    logger.exception('Unhandled error:')
    if debug:
        pdb.post_mortem(sys.exc_info()[2])

exit(retcode)
