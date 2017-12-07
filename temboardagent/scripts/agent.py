from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
from socket import getfqdn
import logging
from multiprocessing import Process, Queue
import os
import signal

from ..cli import cli, define_common_arguments
from ..sharedmemory import Commands, Sessions
from ..async import Scheduler
from ..configuration import load_configuration, OptionSpec
from ..daemon import (
    daemonize,
    httpd_sigterm_handler,
    set_global_scheduler,
    httpd_sighup_handler,
)
from ..httpd import httpd_run
from ..queue import purge_queue_dir
from .. import validators as v


logger = logging.getLogger(__name__)


def define_arguments(parser):
    define_common_arguments(parser)
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
    all_plugins = [
        "activity",
        "administration",
        "dashboard",
        "monitoring",
        "pgconf",
    ]
    yield OptionSpec(
        section, 'plugins', default=all_plugins, validator=v.jsonlist,
    )

    s = 'postgresql'
    yield OptionSpec(
        s, 'host', default='/var/run/postgresql', validator=v.dir_)
    yield OptionSpec(s, 'instance', default='main')
    yield OptionSpec(s, 'port', default=5432, validator=v.port)
    yield OptionSpec(s, 'user', default='postgres')
    yield OptionSpec(s, 'password')
    yield OptionSpec(s, 'dbname', default='postgres')

    s = 'logging'
    yield OptionSpec(s, 'method', default='syslog', validator=v.logmethod)
    yield OptionSpec(s, 'level', default='INFO', validator=v.loglevel)
    yield OptionSpec(
        s, 'facility', default='local0', validator=v.syslogfacility,
    )
    yield OptionSpec(s, 'destination', default='/dev/log')


@cli
def main(argv, environ):
    parser = ArgumentParser(
        prog='temboard-agent',
        description="temBoard agent.",
        argument_default=UNDEFINED_ARGUMENT,
    )
    define_arguments(parser)
    args = parser.parse_args(argv)
    config = load_configuration(
        specs=list_options_specs(),
        args=args, environ=environ,
    )

    # Run temboard-agent as a background daemon.
    if (config.temboard.daemonize):
        daemonize(config.temboard.pidfile)

    config.setup_logging()
    logger.info("Starting main process.")

    # Purge all data queues at start time excepting metrics & notifications.
    purge_queue_dir(config.temboard['home'],
                    ['metrics.q', 'notifications.q', 'notifications_last_10.q']
                    )

    # Creation of the command list (max 100).
    commands = Commands(100)
    # Creation of the session list (max 100).
    sessions = Sessions(100)
    # Command queue creation.
    queue_in = Queue()

    # Start the command scheduler process.
    scheduler = Process(target=Scheduler,
                        args=(commands, queue_in, config, sessions))
    scheduler.start()

    # Let's store scheduler reference in a global var.
    set_global_scheduler(scheduler)
    # Add signal handlers on SIGTERM and SIGHUP.
    signal.signal(signal.SIGTERM, httpd_sigterm_handler)
    signal.signal(signal.SIGHUP, httpd_sighup_handler)

    # Serve HTTPS forever.
    httpd_run(commands, queue_in, config, sessions)

    # Join command scheduler process on http server process exit.
    scheduler.join()

    return 0


if __name__ == '__main__':  # pragma: no cover
    main()
