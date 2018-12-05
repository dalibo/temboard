import atexit
import os
import sys

PIDFILE = None


def remove_pidfile(pidfile):
    """
    Delete the pidfile.
    """
    if pidfile:
        try:
            os.remove(pidfile)
        except OSError:
            pass


def daemonize(pidfile, config):
    """
    Run temboard as a background daemon.
    Inspired by:
    http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
    """
    # Try to read pidfile
    try:
        with open(pidfile, 'r') as pf:
            pid = int(pf.read().strip())
    except IOError:
        pid = None
    except ValueError:
        sys.stderr.write("WARNING: pidfile %s in wrong format.\n" % pidfile)
        pid = -1

    # If pidfile exists, yet another temboard is probably running.
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
        sys.stderr.write("FATAL: fork failed: %d (%s)\n" % (e.errno,
                                                            e.strerror))
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
        sys.stderr.write("FATAL: fork failed: %d (%s)\n" % (e.errno,
                                                            e.strerror))
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
