"""

Logging things should follow this template:

[INFO] "We are going to do something"
[DEBUG] Raw data, when we're working with data
if error:
    [ERROR] Error message with exception
    [INFO] "Failed."
else:
    [INFO] "Done."

"""


from logging import Formatter
from logging.handlers import SysLogHandler


class MultilineFormatter(Formatter):
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


LOG_METHODS = {
    'stderr': {
        '()': 'logging.StreamHandler',
        'formatter': 'full',
    },
    'file': {
        '()': 'logging.FileHandler',
        'mode': 'a',
        'formatter': 'minimal',
    },
    'syslog': {
        '()': 'logging.handlers.SysLogHandler',
        'formatter': 'minimal',
    }
}


def generate_logging_config(config):
    LOG_METHODS['file']['filename'] = config.logging['destination']
    facility = SysLogHandler.facility_names[config.logging['facility']]
    LOG_METHODS['syslog']['facility'] = facility
    LOG_METHODS['syslog']['address'] = config.logging['destination']

    format_ = (
        "temboard[%(process)5d]: [%(name)-24s] %(levelname)8s: "
        "%(message)s"
    )

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'minimal': {
                '()': 'temboardui.logger.MultilineFormatter',
                'format': format_,
            },
            'full': {
                '()': 'temboardui.logger.MultilineFormatter',
                'format': '%(asctime)s ' + format_,
            }
        },
        'handlers': {
            'configured': LOG_METHODS[config.logging['method']]
        },
        'root': {
            'level': 'INFO',
            'handlers': ['configured'],
        },
        'loggers': {
            'temboardui': {
                'level': config.logging['level'],
            },
        },
    }

    return logging_config
