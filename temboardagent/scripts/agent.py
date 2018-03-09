# coding: utf-8

from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
from socket import getfqdn
import logging
import os
import signal

from temboardsched import taskmanager

from ..cli import bootstrap
from ..cli import cli, define_core_arguments
from ..sharedmemory import Sessions
from ..configuration import OptionSpec
from ..daemon import (
    daemonize,
    httpd_sigterm_handler,
    httpd_sighup_handler,
)
from ..httpd import httpd_run
from ..queue import purge_queue_dir
from .. import validators as v


logger = logging.getLogger('temboardagent.scripts.agent')


def define_arguments(parser):
    define_core_arguments(parser)
    parser.add_argument(
        '-d', '--daemon',
        action='store_true', dest='temboard_daemonize',
        help="Run in background.",
    )
    parser.add_argument(
        '-p', '--pid-file',
        action='store', dest='temboard_pidfile',
        help="PID file.",
    )


def list_options_specs():
    # Generate each option specs.
    section = 'temboard'
    yield OptionSpec(section, 'daemonize', default=False)
    yield OptionSpec(section, 'pidfile', default='/run/temboard-agent.pid')
    yield OptionSpec(
        section, 'address', default='0.0.0.0', validator=v.address)
    yield OptionSpec(section, 'port', validator=v.port, default=2345)
    yield OptionSpec(
        section, 'ssl_cert_file',
        default=OptionSpec.REQUIRED, validator=v.file_)
    yield OptionSpec(
        section, 'ssl_key_file',
        default=OptionSpec.REQUIRED, validator=v.file_)
    yield OptionSpec(section, 'ssl_ca_cert_file', validator=v.file_)
    yield OptionSpec(section, 'key')
    yield OptionSpec(
        section, 'users',
        default='/etc/temboard-agent/users', validator=v.file_,
    )
    yield OptionSpec(section, 'hostname', default=getfqdn())
    home = os.environ.get('HOME', '/var/lib/temboard-agent')
    yield OptionSpec(section, 'home', default=home, validator=v.writeabledir)


@cli
def main(argv, environ):
    parser = ArgumentParser(
        prog='temboard-agent',
        description="temBoard agent.",
        argument_default=UNDEFINED_ARGUMENT,
    )
    define_arguments(parser)
    args = parser.parse_args(argv)
    app = bootstrap(
        specs=list_options_specs(),
        args=args, environ=environ,
    )
    config = app.config

    # Run temboard-agent as a background daemon.
    if (config.temboard.daemonize):
        daemonize(config.temboard.pidfile)

    logger.info("Starting main process.")

    # Purge all data queues at start time excepting metrics & notifications.
    purge_queue_dir(config.temboard['home'],
                    ['metrics.q', 'notifications.q', 'notifications_last_10.q']
                    )

    # Creation of the session list (max 100).
    sessions = Sessions(100)

    # TaskManager
    # Remove socket if any
    tm_sock_path = os.path.join(config.temboard['home'], '.tm.socket')
    if os.path.exists(tm_sock_path):
        os.unlink(tm_sock_path)

    tm = taskmanager.TaskManager(
            task_path=str(os.path.join(config.temboard['home'],
                                       '.tm.task_list')),
            address=str(tm_sock_path)
         )
    # copy configuration into context as a dict
    tm.set_context('config', {'plugins': config.plugins.__dict__.get('data'),
                              'temboard': config.temboard.__dict__.get('data'),
                              'postgresql': config.postgresql.__dict__.get('data'),
                              'logging': config.logging.__dict__.get('data')})
    tm.start()

    # Add signal handlers on SIGTERM and SIGHUP.
    signal.signal(signal.SIGTERM, httpd_sigterm_handler)
    signal.signal(signal.SIGHUP, httpd_sighup_handler)

    # Serve HTTPS forever.
    httpd_run(app, sessions)

    return 0


if __name__ == '__main__':  # pragma: no cover
    main()
