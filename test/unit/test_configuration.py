# -*- coding: utf-8 -*-

import pytest


def test_spec_and_value():
    from temboardagent.configuration import OptionSpec, Value

    spec = OptionSpec(section='temboard', name='verbose', default=False)
    assert repr(spec)

    value = Value('temboard_verbose', True, origin='test')
    assert repr(value)

    assert value.name in {spec}


def test_load(mocker):
    mocker.patch('temboardagent.configuration.MergedConfiguration.load_file')
    mocker.patch('temboardagent.configuration.MergedConfiguration.load_legacy')
    mocker.patch('temboardagent.configuration.load_plugins_configurations')
    # Bypass file validation
    mocker.patch('temboardagent.configuration.v.file_', None)

    from argparse import Namespace
    from temboardagent.configuration import OptionSpec, load_configuration

    specs = [
        # to test argument parsing
        OptionSpec(section='temboard', name='fromarg', default='DEFVAL'),
        # to test environment parsing
        OptionSpec(section='temboard', name='fromenv', default='DEFVAL'),
        # to test default value
        OptionSpec(section='temboard', name='fromdefault', default='DEFVAL'),
    ]
    args = Namespace(temboard_fromarg='ARGVAL')
    environ = dict(
        TEMBOARD_FROMENV='ENVVAL',
        # These should be ignored
        TEMBOARD_FROMARG='ENVAL',
        PATH='',
    )
    config = load_configuration(specs=specs, args=args, environ=environ)

    assert 'DEFVAL' == config.temboard.fromdefault
    assert 'ARGVAL' == config.temboard.fromarg
    assert 'ENVVAL' == config.temboard.fromenv
    assert config.temboard.configfile.startswith('/etc/temboard-agent/')
    assert config.loaded is True


def test_load_invalid_from_user(mocker):
    file_ = mocker.patch('temboardagent.configuration.v.file_')
    file_.side_effect = ValueError()

    from temboardagent.configuration import (
        load_configuration,
        UserError,
    )

    environ = dict(TEMBOARD_CONFIGFILE=__file__ + 'ne pas créer !')
    with pytest.raises(UserError):
        load_configuration(environ=environ)


def test_load_invalid_default(mocker):
    mocker.patch('temboardagent.configuration.MergedConfiguration.load_file')
    mocker.patch('temboardagent.configuration.MergedConfiguration.load_legacy')
    mocker.patch('temboardagent.configuration.load_plugins_configurations')
    # Bypass file validation
    mocker.patch('temboardagent.configuration.v.file_', None)

    validator = mocker.Mock(side_effect=ValueError())

    from temboardagent.configuration import OptionSpec, load_configuration

    specs = [
        OptionSpec('section', 'name', default='invalid', validator=validator),
    ]

    with pytest.raises(ValueError):
        load_configuration(specs=specs, environ={})


def test_legacy(mocker):
    Configuration = mocker.patch('temboardagent.configuration.Configuration')

    from temboardagent.configuration import MergedConfiguration, configparser

    configparser = configparser.RawConfigParser()
    configparser.temboard = {'port': 8080}
    configparser.configfile = 'configfile'
    configparser.confdir = 'confdir'

    Configuration.return_value = configparser

    config = MergedConfiguration()
    config.temboard = dict(configfile='mock')

    config.load_legacy()

    assert 8080 == config.temboard.port
    assert 'configfile' == config.configfile
    assert 'confdir' == config.confdir


def test_load_configparser():
    from temboardagent.configuration import (
        configparser,
        iter_configparser_values,
    )

    parser = configparser.RawConfigParser()
    parser.add_section('section0')
    parser.set('section0', 'option0', 'pouet')

    values = list(iter_configparser_values(parser, 'my.cfg'))

    assert 1 == len(values)
    assert 'pouet' == values[0].value
    assert 'section0_option0' == values[0].name
    assert 'my.cfg' == values[0].origin


def test_logging():
    from temboardagent.configuration import generate_logging_config, DotDict

    config = DotDict(dict(logging=dict(
        destination='pouet',
        facility='local0',
        method='stderr',
        level='DEBUG',
    )))

    generate_logging_config(**config)
