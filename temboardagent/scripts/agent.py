from argparse import ArgumentParser, SUPPRESS as UNDEFINED_ARGUMENT
import logging
from multiprocessing import Process, Queue
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


logger = logging.getLogger(__name__)


def define_arguments(parser):
    define_common_arguments(parser)
    parser.add_argument(
        '-d', '--daemon',
        action='store_true', dest='temboard_daemonize',
        help="Run in background. Default: %(default)s",
    )
    parser.add_argument(
        '-p', '--pid-file',
        action='store', dest='temboard_pidfile',
        help="PID file. Default: %(default)s",
    )


def list_options_specs():
    # Generate each option specs.
    section = 'temboard'
    yield OptionSpec(section, 'daemonize', False)
    yield OptionSpec(section, 'pidfile', '/run/temboard-agent.pid')


@cli
def main(argv, environ):
    parser = ArgumentParser(
        prog='temboard-agent',
        description="temBoard agent.",
        argument_default=UNDEFINED_ARGUMENT,
    )
    define_arguments(parser)
    args = parser.parse_args(argv)
    config = load_configuration(specs=list_options_specs(), args=args)
    config.setup_logging()
    logger.info("Starting main process.")

    # Run temboard-agent as a background daemon.
    if (config.temboard.daemonize):
        daemonize(config.temboard.pidfile)

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
