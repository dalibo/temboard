from multiprocessing import Process
import signal
from os import getpid

from temboardagent.logger import get_logger, set_logger_name, get_tb
from temboardagent.routing import get_worker
from temboardagent.daemon import (set_global_workers,
                                  scheduler_sigterm_handler,
                                  scheduler_sighup_handler,
                                  set_global_reload,
                                  reload_true, worker_sigterm_handler,
                                  worker_sighup_handler)
from temboardagent.configuration import Configuration
from temboardagent.errors import ConfigurationError
from temboardagent.pluginsmgmt import (load_plugins_configurations,
                                       exec_scheduler)


def Worker(commands, command, config):
    """
    Routing function in charge of calling the right worker function.
    """
    # Add a signal handler on SIGTERM and SIGHUP signals.
    signal.signal(signal.SIGTERM, worker_sigterm_handler)
    signal.signal(signal.SIGHUP, worker_sighup_handler)

    try:
        get_worker(command.worker)(commands, command, config)
    except (AttributeError, Exception) as e:
        set_logger_name("scheduler")
        logger = get_logger(config)
        logger.error(str(e))


def Scheduler(commands, queue_in, config, sessions):
    """
    Asynchronous command scheduler in charge of:
        - fetching new async command from the command queue.
        - if any new command, starting a new worker process.
        - doing maintenance tasks like sessions and commands clean-up.
        - executing function named scheduler() from each loaded plugins.
    """
    set_logger_name("scheduler")
    logger = get_logger(config)

    # Add a signal handler on SIGTERM and SIGHUP signals.
    signal.signal(signal.SIGTERM, scheduler_sigterm_handler)
    signal.signal(signal.SIGHUP, scheduler_sighup_handler)

    logger.debug("Starting with pid=%s", (getpid()))
    workers = []
    while True:
        if reload_true():
            # SIGHUP signal caught.
            try:
                logger.info("SIGHUP signal caught, trying to reload"
                            " configuration.")
                new_config = Configuration(config.configfile)
                # Prevent any change on plugins list..
                new_config.temboard['plugins'] = config.temboard['plugins']
                new_config.plugins = load_plugins_configurations(new_config)
                # Logger re-creation.
                del logger
                set_logger_name("scheduler")
                logger = get_logger(new_config)
                config = new_config
                logger.info("New configuration loaded.")
            except (ConfigurationError, ImportError) as e:
                logger.traceback(get_tb())
                logger.error(str(e))
                logger.info("Some error occured, keeping old configuration.")

            set_global_reload(False)

        try:
            # Fetch one new input from the command queue.
            # There is a 0.5s second timeout and the call isn't blocking.
            command = queue_in.get(True, 0.5)
        except Exception:
            # No new command.
            pass
        else:
            # Start the worker process.
            newworker = Process(target=Worker,
                                args=(commands, command, config))
            workers.append(newworker)
            newworker.start()

        # Check that worker processes are still alive.
        for worker in workers:
            if not worker.is_alive():
                worker.join()
                workers.remove(worker)

        # Let store workers in a global var.
        set_global_workers(workers)
        # Execute plugins scheduler() function.
        exec_scheduler(queue_in, config, commands, logger)
        # Purge expired sessions if any.
        sessions.purge_expired(3600, logger, config)
        # Remove old unchecked commands.
        commands.purge_expired(60, logger)
