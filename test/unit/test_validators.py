# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os.path

import pytest

from temboardagent import validators as v


def test_address():
    assert v.address('0.0.0.0')
    assert v.address('127.0.0.1')

    with pytest.raises(ValueError):
        v.address('127')

    with pytest.raises(ValueError):
        v.address('127.0.0.0.0.0')

    with pytest.raises(ValueError):
        v.address('localhost')


def test_boolean():
    assert v.boolean('y') is True
    assert v.boolean('0') is False
    assert v.boolean('yes') is True
    assert v.boolean(True) is True

    with pytest.raises(ValueError):
        v.boolean('pouet')


def test_directory(mocker):
    access = mocker.patch('temboardagent.validators.os.access')

    access.return_value = True
    assert v.writeabledir(os.path.dirname(__file__))

    access.return_value = False
    with pytest.raises(ValueError):
        v.writeabledir('/usr')


def test_file():
    assert v.file_(__file__) == __file__
    relpath = os.path.relpath(__file__)
    assert v.file_(relpath) == __file__

    with pytest.raises(ValueError):
        v.file_(__file__ + 'ne pas créer')


def test_jsonlist():
    assert ['a'] == v.jsonlist(['a'])
    assert ['a'] == v.jsonlist('["a"]')

    with pytest.raises(ValueError):
        v.jsonlist('{}')

    with pytest.raises(ValueError):
        v.jsonlist('["!"]')


def test_loglevel():
    assert 'DEBUG' == v.loglevel('DEBUG')
    assert 'INFO' == v.loglevel('info')

    with pytest.raises(ValueError):
        v.loglevel('pouet')


def test_logmethod():
    assert 'stderr' == v.logmethod('stderr')

    with pytest.raises(ValueError):
        v.logmethod('pouet')


def test_port():
    assert 8080 == v.port('8080')

    with pytest.raises(ValueError):
        v.port('-1')

    with pytest.raises(ValueError):
        v.port('80000')

    with pytest.raises(ValueError):
        v.port('pouet')
