from __future__ import unicode_literals

import logging


logger = logging.getLogger('temboardagent.' + __name__)


class Hello(object):
    def __init__(self):
        logger.info("hello code running. Over.")


class Failing(object):
    def __init__(self):
        assert False, "Plugins fails to load."
