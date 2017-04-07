import sys
import traceback
import socket
from logging import (Logger, Formatter, DEBUG, INFO, WARNING, ERROR, CRITICAL,
                     FileHandler, StreamHandler)
from logging.handlers import SysLogHandler
from temboardagent.errors import ConfigurationError


"""

Logging things should follow this template:

[INFO] "We are going to do something"
[DEBUG] Raw data, when we're working with data
if error:
    [DEBUG] Error backtrace
    [ERROR] Error message from the exception
    [INFO] "Failed."
else:
    [INFO] "Done."

"""


def get_tb():
    exc_info = sys.exc_info()
    lines = traceback.format_exc().splitlines()
    del exc_info
    return lines


# Mapping configuration -> constants
LOG_FACILITIES = {
    'local0': SysLogHandler.LOG_LOCAL0,
    'local1': SysLogHandler.LOG_LOCAL1,
    'local2': SysLogHandler.LOG_LOCAL2,
    'local3': SysLogHandler.LOG_LOCAL3,
    'local4': SysLogHandler.LOG_LOCAL4,
    'local5': SysLogHandler.LOG_LOCAL5,
    'local6': SysLogHandler.LOG_LOCAL6,
    'local7': SysLogHandler.LOG_LOCAL7
}

LOG_LEVELS = {
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARNING': WARNING,
    'ERROR': ERROR,
    'CRITICAL': CRITICAL
}

LOG_METHODS = ['syslog', 'file', 'stderr']


class Log(Logger):
    """
    Logger
    """
    _instances = dict()

    def __new__(cls, config, name, *args, **kwargs):
        # Create a new logger only once.
        if name not in cls._instances:
            inst = super(Log, cls).__new__(cls)
            cls._instances[name] = inst
        return cls._instances[name]

    def __init__(self, config, name, *args, **kwargs):
        Logger.__init__(self, name, *args, **kwargs)

        log_format = "temboard-agent[%(process)d]: [%(name)s] %(levelname)s:"\
                     " %(message)s"

        if config.logging['method'] == 'syslog':
            try:
                # Instanciate a new syslog handler.
                lh = SysLogHandler(
                        address=str(config.logging['destination']),
                        facility=LOG_FACILITIES[config.logging['facility']])
            except socket.error as e:
                raise ConfigurationError(e)
        elif config.logging['method'] == 'file':
            try:
                # Instanciate a new file handler.
                lh = FileHandler(
                        filename=config.logging['destination'],
                        mode='a')
                # Add timestamp when using a FileHandler.
                log_format = "%(asctime)s "+log_format
            except IOError as e:
                raise ConfigurationError(e)
        elif config.logging['method'] == 'stderr':
            lh = StreamHandler()
            # Add timestamp
            log_format = "%(asctime)s "+log_format

        # Set log level according to the level defined in configuration files.
        lh.setLevel(LOG_LEVELS[config.logging['level']])
        lh.setFormatter(Formatter(log_format))
        self.addHandler(lh)

    def traceback(self, tb_lines):
        if isinstance(tb_lines, list):
            for l in tb_lines:
                self.debug(l)
        else:
            self.debug(tb_lines)


LOGGER_NAME = 'temboard-agent'


def set_logger_name(name):
    global LOGGER_NAME
    LOGGER_NAME = name


def get_logger(config):
    """
    Returns a logger instance.
    """
    return Log(config, LOGGER_NAME)
