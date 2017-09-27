import logging
from logging.handlers import SysLogHandler


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

LOG_FACILITIES = SysLogHandler.facility_names
LOG_LEVELS = logging._levelNames.values()
LOG_FORMAT = (
    "temboard-agent[%(process)d]: [%(name)s] %(levelname)s: %(message)s"
)


def generate_logging_config(config):
    LOG_METHODS['file']['filename'] = config.logging['destination']
    facility = SysLogHandler.facility_names[config.logging['facility']]
    LOG_METHODS['syslog']['facility'] = facility
    LOG_METHODS['syslog']['address'] = config.logging['destination']

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'minimal': {
                'format': LOG_FORMAT,
            },
            'full': {
                'format': '%(asctime)s ' + LOG_FORMAT,
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
            'temboardagent': {
                'level': config.logging['level'],
            },
            'temboard-agent': {
                'level': config.logging['level'],
            },
        },
    }
    return logging_config
