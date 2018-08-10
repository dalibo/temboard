# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os.path

import pytest

from sampleproject.toolkit import validators as v


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
    access = mocker.patch('sampleproject.toolkit.validators.os.access')
    isdir = mocker.patch('sampleproject.toolkit.validators.os.path.isdir')

    access.return_value = True
    isdir.return_value = True
    assert v.writeabledir(os.path.dirname(__file__))

    access.return_value = False
    with pytest.raises(ValueError):
        v.writeabledir('/usr')

    access.return_value = True
    isdir.return_value = False
    with pytest.raises(ValueError):
        v.writeabledir('/usr')


def test_file():
    assert v.file_(__file__) == __file__
    relpath = os.path.relpath(__file__)
    assert v.file_(relpath) == __file__

    assert not v.file_(None)
    assert not v.file_('')

    with pytest.raises(ValueError):
        v.file_(__file__ + 'ne pas créer')


def test_jsonlist():
    assert ['a'] == v.jsonlist(['a'])
    assert ['a'] == v.jsonlist('["a"]')

    with pytest.raises(ValueError):
        v.jsonlist('{}')

    with pytest.raises(ValueError):
        v.jsonlist('["!"]')


def test_commalist():
    assert ['a', 'b'] == v.commalist('a,,b')


def test_loglevel():
    assert 'DEBUG' == v.loglevel('DEBUG')
    assert 'INFO' == v.loglevel('info')

    with pytest.raises(ValueError):
        v.loglevel('pouet')


def test_logmethod():
    assert 'stderr' == v.logmethod('stderr')

    with pytest.raises(ValueError):
        v.logmethod('pouet')


def test_syslog_facility():
    assert 'local0' == v.syslogfacility('local0')

    with pytest.raises(ValueError):
        v.syslogfacility('pouet')


def test_port():
    assert 8080 == v.port('8080')

    with pytest.raises(ValueError):
        v.port('-1')

    with pytest.raises(ValueError):
        v.port('80000')

    with pytest.raises(ValueError):
        v.port('pouet')


def test_quoted():
    assert 'double-quoted' == v.quoted('"double-quoted"')
    assert 'single-quoted' == v.quoted("'single-quoted'")
    assert '"not quoted' == v.quoted('"not quoted')
