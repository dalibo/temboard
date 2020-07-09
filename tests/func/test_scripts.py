from __future__ import absolute_import

from .test.temboard import exec_command


def test_register_help():
    rc, out, err = exec_command(["temboard-agent-register", "--help"])
    assert 0 == rc, err
