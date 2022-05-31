import logging
from logging.config import dictConfig
from logging.handlers import SysLogHandler
import sys


class ColoredStreamHandler(logging.StreamHandler):

    _color_map = {  # Colors code from systemctl/journalctl
        logging.DEBUG: '38;5;245',
        logging.INFO: '1;39',
        logging.WARN: '38;5;185',
        logging.ERROR: '31',
        logging.CRITICAL: '1;91',
    }

    def format(self, record):
        lines = logging.StreamHandler.format(self, record)
        color = self._color_map.get(record.levelno, '39')
        lines = ''.join([
            '\033[0;%sm%s\033[0m' % (color, line)
            for line in lines.splitlines(True)
        ])
        return lines


class MultilineFormatter(logging.Formatter):
    def format(self, record):
        s = logging.Formatter.format(self, record)
        if '\n' in s:
            s = s.replace('\n', '\n\t')
        return s


class NullHandler(logging.Handler):
    def handle(self, record):
        pass

    def emit(self, record):
        pass

    def createLock(self):
        self.lock = None


class SystemdFormatter(MultilineFormatter):
    # cf. http://0pointer.de/blog/projects/journal-submit.html
    priority_map = {
        logging.NOTSET: 6,
        logging.DEBUG: 7,
        logging.INFO: 6,
        logging.WARNING: 4,
        logging.ERROR: 3,
        logging.CRITICAL: 2,
    }

    def format(self, record):
        s = MultilineFormatter.format(self, record)
        prefix = '<%d>' % self.priority_map[record.levelno]
        lines = [prefix + line for line in s.splitlines(True)]
        return ''.join(lines)


class LastnameFilter(logging.Filter):
    root, _, _ = __name__.partition('.')

    def filter(self, record):
        record.lastname = record.name
        if record.name.startswith(self.root + '.'):
            _, record.lastname = record.name.rsplit('.', 1)
        # Always log, we are just enriching records.
        return 1


HANDLERS = {
    'file': {
        '()': 'logging.FileHandler',
        'mode': 'a',
        'formatter': 'dated_syslog',
    },
    'syslog': {
        '()': 'logging.handlers.SysLogHandler',
        'formatter': 'syslog',
    },
    'stderr': {
        '()': __name__ + '.NullHandler',
    }
}


def setup_logging(**kw):
    logging_config = generate_logging_config(**kw)
    dictConfig(logging_config)


def configure_debug(logging_config, core, debug):
    # If --debug or DEBUG=1, apply DEBUG to all core loggers
    if debug in (True, '__debug__'):
        debug = core

    if hasattr(debug, 'split'):
        debug = filter(None, debug.split(','))

    # Now apply debug level.
    if debug:
        for loggername in debug:
            logger = logging_config['loggers'].setdefault(loggername, {})
            logger['level'] = 'DEBUG'


def generate_logging_config(
        level=None, destination=None, facility='local0',
        method='stderr', debug=None, systemd=False, **kw):
    # Our logging strategy is to always log on stderr and allow to log on
    # either syslog or a file, depending on user configuration.
    #
    # stderr mean either console when launching in a terminal, file when stderr
    # is piped or systemd output. Thus we adapt stderr to these cases depending
    # on systemd an isatty().

    core = LastnameFilter.root

    if level is None:
        level = 'DEBUG' if debug else 'INFO'

    if debug is None:
        debug = level == 'DEBUG'

    verbose = debug or level == 'DEBUG'

    facility = SysLogHandler.facility_names[facility]
    HANDLERS['syslog']['facility'] = facility
    HANDLERS['syslog']['address'] = destination
    HANDLERS['file']['filename'] = destination

    stderr_handler = 'logging.StreamHandler'
    if sys.stderr.isatty():
        stderr_handler = __name__ + '.ColoredStreamHandler'

    minimal_fmt = '%(levelname)s:  %(lastname)s: %(message)s'
    verbose_fmt = '%(asctime)s ' + core + '[%(process)d] ' + minimal_fmt
    syslog_fmt = (
        core + "[%(process)d] %(levelname)s:  %(lastname)s: %(message)s"
    )

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'lastname': {
                '()': __name__ + '.LastnameFilter',
            }
        },
        'formatters': {
            'console': {
                '()': __name__ + '.MultilineFormatter',
                'format': verbose_fmt if verbose else minimal_fmt,
                'datefmt': '%Y-%m-%d %H:%M:%S %Z',
            },
            'dated_syslog': {
                '()': __name__ + '.MultilineFormatter',
                'format': '%(asctime)s ' + syslog_fmt,
                'datefmt': '%Y-%m-%d %H:%M:%S %Z',
            },
            'syslog': {
                '()': __name__ + '.MultilineFormatter',
                'format': syslog_fmt,
            },
            'systemd': {
                '()': __name__ + '.SystemdFormatter',
                'format': '%(lastname)s: %(message)s',
            }
        },
        'handlers': {
            'configured': dict(
                HANDLERS[method],
                filters=['lastname'],
            ),
            'stderr': {
                '()': stderr_handler,
                'formatter': 'systemd' if systemd else 'console',
                'filters': ['lastname'],
            },
        },
        'root': {
            'level': 'INFO',
            # Avoid instanciate all handlers, especially syslog which open
            # /dev/log
            'handlers': ['stderr', 'configured'],
        },
        'loggers': {},
    }

    # Apply level to temboard loggers only
    logging_config['loggers'][core] = dict(level=level)

    configure_debug(logging_config, core, debug)

    return logging_config
