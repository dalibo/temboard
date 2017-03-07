#!/bin/bash -eux

me=$(readlink -e ${0})
worktree=${me%/*/*.sh}
cd $worktree

if ! hash pip ; then
    curl "https://bootstrap.pypa.io/get-pip.py" | python -
    yum -y install python-devel gcc
fi

if ! pip freeze | grep -q '#egg=temboard' ; then
    pip install -e .
    chown -R $(stat -c %u.%g setup.py) temboard.egg-info
fi

# Run temboard in the background and wait for ever. This allow to kill temboard
# without killing the container.
temboard --daemon
exec ${*-tail -f /dev/null}
