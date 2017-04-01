import sys
import os
import atexit
import signal
import time

# Some global vars we need to have because signal handler function can't take
# extra parameters.
PIDFILE = None
SCHEDULER = None
WORKERS = None
RELOAD = False


def set_global_workers(workers):
    global WORKERS
    WORKERS = workers


def set_global_scheduler(scheduler):
    global SCHEDULER
    SCHEDULER = scheduler


def set_global_reload(value):
    global RELOAD
    RELOAD = value


def reload_true():
    return RELOAD


def httpd_sighup_handler(signum, frame):
    """
    SIGHUP handler for httpd process.
    """
    set_global_reload(True)
    if SCHEDULER:
        # Send a SIGHUP signal to the scheduler.
        os.kill(SCHEDULER.pid, signal.SIGHUP)


def scheduler_sighup_handler(signum, frame):
    """
    SIGHUP handler for scheduler process.
    """
    set_global_reload(True)
    if WORKERS:
        for worker in WORKERS:
            if worker.is_alive():
                worker_pid = worker.pid
                if worker_pid:
                    os.kill(worker_pid, signal.SIGHUP)
            time.sleep(0.5)


def httpd_sigterm_handler(signum, frame):
    """
    SIGTERM signal handler for httpd process.
    """
    if SCHEDULER:
        # Send a SIGTERM signal to the scheduler.
        os.kill(SCHEDULER.pid, signal.SIGTERM)
        # Wait until it dies, because while it's alive, some workers may be
        # running and we want to wait until all workers finish their work
        # before exiting.
        while True:
            if not SCHEDULER.is_alive():
                SCHEDULER.join()
                break
            time.sleep(0.5)
    # Remove the pidfile.
    remove_pidfile(PIDFILE)
    # Exit roughly with os._exit() because httpd is multi-threaded and
    # sys.exit() does not work in this context.
    os._exit(1)


def scheduler_sigterm_handler(signum, frame):
    """
    SIGTEMR signal handler for scheduler process.
    """
    if WORKERS:
        n_dead_worker = 0
        while n_dead_worker < len(WORKERS):
            # Wait until all worker processes are dead.
            n_dead_worker = 0
            for worker in WORKERS:
                if worker.is_alive():
                    worker_pid = worker.pid
                    if worker_pid:
                        os.kill(worker_pid, signal.SIGTERM)
                if not worker.is_alive():
                    worker.join()
                    n_dead_worker += 1
                    WORKERS.remove(worker)
            time.sleep(0.5)
    sys.exit(1)


def worker_sigterm_handler(signum, frame):
    """
    Default SIGTERM signal handler for the workers.
    """
    return


def worker_sighup_handler(signum, frame):
    """
    Default SIGHUP signal handler for the workers.
    """
    return


def remove_pidfile(pidfile):
    """
    Delete the pidfile.
    """
    if pidfile:
        try:
            os.remove(pidfile)
        except OSError:
            pass


def daemonize(pidfile):
    """
    Run temboard-agent as a background daemon.
    Inspired by:
    http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
    """
    # Try to read pidfile
    try:
        with open(pidfile, 'r') as pf:
            pid = int(pf.read().strip())
    except IOError:
        pid = None

    # If pidfile exists, yet another process is probably running.
    if pid:
        sys.stderr.write("FATAL: pidfile %s already exist.\n" % pidfile)
        sys.exit(1)

    # Try to write pidfile.
    try:
        with open(pidfile, 'w+') as pf:
            pf.write("\0")
    except IOError:
        sys.stderr.write("FATAL: can't write pidfile %s.\n" % pidfile)
        sys.exit(1)

    # First fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Exit first parent.
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("FATAL: fork failed: %d (%s)\n"
                         % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # Do second fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from second parent.
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("FATAL: fork failed: %d (%s)\n"
                         % (e.errno, e.strerror))
        sys.exit(1)

    # Redirect standard file descriptors.
    sys.stdout.flush()
    sys.stderr.flush()
    si = file('/dev/null', 'r')
    so = file('/dev/null', 'a+')
    se = file('/dev/null', 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    # write pidfile
    atexit.register(remove_pidfile, pidfile)
    pid = str(os.getpid())
    with open(pidfile, 'w+') as pf:
        pf.write("%s\n" % pid)
    global PIDFILE
    PIDFILE = pidfile
