import logging.config
from logging.handlers import SysLogHandler
import sys


class ColoredStreamHandler(logging.StreamHandler):

    _color_map = {
        logging.DEBUG: '37',
        logging.INFO: '1;39',
        logging.WARN: '96',
        logging.ERROR: '91',
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


class LastnameFilter(logging.Filter):
    def filter(self, record):
        record.lastname = record.name
        if record.name.startswith('temboardagent.'):
            _, record.lastname = record.name.rsplit('.', 1)
        # Always log, we are just enriching records.
        return 1


class MultilineFormatter(logging.Formatter):
    def format(self, record):
        s = super(MultilineFormatter, self).format(record)
        if '\n' not in s:
            return s

        lines = s.splitlines()
        d = record.__dict__.copy()
        for i, line in enumerate(lines[1:]):
            record.message = line
            lines[1+i] = self._fmt % record.__dict__
        record.__dict__ = d

        return '\n'.join(lines)


HANDLERS = {
    'stderr': {
        '()': 'logging.StreamHandler',
        'formatter': 'minimal',
    },
    'file': {
        '()': 'logging.FileHandler',
        'mode': 'a',
        'formatter': 'dated_syslog',
    },
    'syslog': {
        '()': 'logging.handlers.SysLogHandler',
        'formatter': 'syslog',
    }
}


def generate_logging_config(config):
    facility = SysLogHandler.facility_names[config.logging['facility']]
    level = logging.getLevelName(config.logging['level'])
    method = config.logging['method']
    HANDLERS['file']['filename'] = config.logging['destination']
    HANDLERS['syslog']['facility'] = facility
    HANDLERS['syslog']['address'] = config.logging['destination']
    fmt = 'verbose' if level == 'DEBUG' else 'minimal'
    HANDLERS['stderr']['formatter'] = fmt
    if sys.stderr.isatty():
        HANDLERS['stderr']['()'] = __name__ + '.ColoredStreamHandler'

    minimal_fmt = '%(levelname)5.5s: %(message)s'
    verbose_fmt = '%(asctime)s [%(lastname)-16.16s] ' + minimal_fmt
    syslog_fmt = (
        "temboard-agent[%(process)d]: "
        "[%(lastname)s] %(levelname)s: %(message)s"
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
            'dated_syslog': {
                '()': __name__ + '.MultilineFormatter',
                'format': '%(asctime)s ' + syslog_fmt,
            },
            'minimal': {
                '()': __name__ + '.MultilineFormatter',
                'format': minimal_fmt,
            },
            'syslog': {
                '()': __name__ + '.MultilineFormatter',
                'format': syslog_fmt,
            },
            'verbose': {
                '()': __name__ + '.MultilineFormatter',
                'format': verbose_fmt,
            },
        },
        'handlers': {
            'configured': dict(
                HANDLERS[method],
                filters=['lastname'],
            ),
        },
        'root': {
            'level': 'INFO',
            'handlers': ['configured'],
        },
        'loggers': {
            'temboardui': {
                'level': config.logging['level'],
            },
            'monitoring': {
                'level': config.logging['level'],
            },
            'temboardsched.taskmanager': {
                'level': config.logging['level'],
            },
        },
    }

    return logging_config
