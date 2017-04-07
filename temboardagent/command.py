from subprocess import Popen, PIPE, CalledProcessError, check_call
from shlex import split as shlex_split
import errno


def exec_command(command_args, **kwargs):
    """
    Execute a system command with Popen.
    """
    kwargs.setdefault("stdout", PIPE)
    kwargs.setdefault("stderr", PIPE)
    kwargs.setdefault("stdin", PIPE)
    kwargs.setdefault("close_fds", True)
    try:
        process = Popen(command_args, **kwargs)
    except OSError as err:
        return (err.errno, None, err.strerror)

    (stdout, stderrout) = process.communicate()

    return (process.returncode, stdout, stderrout)


def exec_script(script_args, **kwargs):
    """
    Execute an external script.
    """
    kwargs.setdefault("stderr", PIPE)
    kwargs.setdefault("stdout", PIPE)
    try:
        check_call(script_args, **kwargs)
    except CalledProcessError as err:
        return (err.returncode, None, err.output)
    except IOError as err:
        if err.errno == errno.EPIPE:
            pass

    return (0, None, None)


def oneline_cmd_to_array(command_line):
    """
    Split a command line using shlex module.
    """
    return shlex_split(command_line)
