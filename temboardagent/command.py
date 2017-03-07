from subprocess import Popen, PIPE, CalledProcessError, call, check_call

# Shortcut functions like check_output() do not appear in subprocess
# until python 2.7 and we need to stay compatible with python 2.6 for
# RHEL/CentOS 5 (epel) and 6.
import sys
if sys.version < (2,7,0):
    # This is the code from subprocess in version 2.7.9
    def check_output(*popenargs, **kwargs):
        r"""Run command with arguments and return its output as a byte string.

        If the exit code was non-zero it raises a CalledProcessError.  The
        CalledProcessError object will have the return code in the returncode
        attribute and output in the output attribute.

        The arguments are the same as for the Popen constructor.  Example:

        >>> check_output(["ls", "-l", "/dev/null"])
        'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

        The stdout argument is not allowed as it is used internally.
        To capture standard error in the result, use stderr=STDOUT.

        >>> check_output(["/bin/sh", "-c",
        ...               "ls -l non_existent_file ; exit 0"],
        ...              stderr=STDOUT)
        'ls: non_existent_file: No such file or directory\n'
        """
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = Popen(stdout=PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise CalledProcessError(retcode, cmd, output=output)
        return output
else:
    from subprocess import check_output

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
        rcode = check_call(script_args, **kwargs)
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
