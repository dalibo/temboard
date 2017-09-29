# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os.path

import pytest


def test_boolean():
    from temboardagent.validators import boolean

    assert boolean('y') is True
    assert boolean('0') is False
    assert boolean('yes') is True
    assert boolean(True) is True

    with pytest.raises(ValueError):
        boolean('pouet')


def test_file():
    from temboardagent.validators import file_

    assert file_(__file__) == __file__
    relpath = os.path.relpath(__file__)
    assert file_(relpath) == __file__

    with pytest.raises(ValueError):
        file_(__file__ + 'ne pas créer')
