import argparse

import pytest


def test_spec_and_value():
    from temboardui.toolkit.configuration import OptionSpec, Value

    spec = OptionSpec(section="temboard", name="verbose", default=False)
    assert repr(spec)

    value = Value("temboard_verbose", True, origin="test")
    assert repr(value)

    assert value.name in {spec}


def test_spec_lifetime(mocker):
    from temboardui.toolkit.configuration import (
        OptionSpec,
        MergedConfiguration,
        UserError,
    )

    def my_validator(x):
        if x == "__ERROR__":
            raise ValueError("Triggered error")
        return x

    config = MergedConfiguration()

    environ = dict(TEMBOARD_MY_OPT=b"__ERROR__")

    # Start with an empty configuration, nothing is loaded.
    config.load(environ=environ)
    assert "my" not in config

    # Extend configuration by adding a spec.
    config.add_specs(
        [OptionSpec("my", "opt", default="defval", validator=my_validator)]
    )

    with pytest.raises(UserError):
        config.load(environ=environ)

    environ = dict(TEMBOARD_MY_OPT="envval")
    config.load(environ=environ)
    assert "my" in config
    assert "envval" == config.my.opt

    # Change source. That could be a file.
    environ = dict(TEMBOARD_MY_OPT="new_envval")

    config.load(environ=environ)
    # Ensure envval is *not* reloaded
    assert "envval" == config.my.opt

    # Assert source is properly reread.
    config.load(environ=environ, reload_=True)
    assert "new_envval" == config.my.opt


def test_argument_for_spec(capsys):
    from temboardui.toolkit.configuration import OptionSpec

    parser = argparse.ArgumentParser()
    spec = OptionSpec("section", "name", default=2345)

    spec.add_argument(parser, "--section-name", help="Name: percent%% %(default)s")

    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    out, _ = capsys.readouterr()
    assert "--section-name SECTION_NAME" in out
    assert "Name: percent% 2345" in out

    args = parser.parse_args([])
    assert not hasattr(args, "section_name")

    args = parser.parse_args(["--section-name=toto"])
    assert "toto" == args.section_name


def test_remove_specs():
    from temboardui.toolkit.configuration import OptionSpec, MergedConfiguration

    def my_validator(x):
        if x == "__ERROR__":
            raise ValueError("Triggered error")
        return x

    config = MergedConfiguration()
    specs = [OptionSpec("my", "opt", default="defval", validator=my_validator)]
    config.add_specs(specs)

    environ = dict(TEMBOARD_MY_OPT="envval")
    config.load(environ=environ)

    # Remove specs
    config.remove_specs(specs)
    # Ensure value is unloaded from config
    assert "my" not in config

    # Ensure value is not reread from env. It should trigger an error if its
    # read.
    environ = dict(TEMBOARD_MY_OPT="__ERROR__")
    config.load(environ=environ, reload_=True)
    assert "my" not in config

    # Remove spec twice.
    config.remove_specs(specs)


def test_load(mocker):
    mocker.patch("temboardui.toolkit.configuration.os.chdir")

    from argparse import Namespace
    from temboardui.toolkit.configuration import OptionSpec, MergedConfiguration
    from temboardui.toolkit.app import configparser

    s = "temboard"
    specs = [
        # to test argument parsing
        OptionSpec(section=s, name="fromarg", default="DEFVAL"),
        # to test environment parsing
        OptionSpec(section=s, name="fromenv", default="DEFVAL"),
        # to test file loading
        OptionSpec(section=s, name="fromfile", default="DEFVAL"),
        # to test default value
        OptionSpec(section=s, name="fromdefault", default="DEFVAL"),
    ]
    args = Namespace(temboard_fromarg="ARGVAL")
    environ = dict(
        TEMBOARD_FROMENV="ENVVAL",
        # These should be ignored.
        TEMBOARD_FROMARG="ENVVAL",
        PATH="",
    )
    parser = configparser.RawConfigParser()
    parser.add_section(s)
    parser.set(s, "fromfile", "FILEVAL")
    # These should be ignored.
    parser.set(s, "fromenv", "FILEVAL")
    parser.set(s, "fromarg", "FILEVAL")

    config = MergedConfiguration(specs=specs)
    config.load(args=args, environ=environ, parser=parser, pwd="/pouet")

    assert "DEFVAL" == config.temboard.fromdefault
    assert "ARGVAL" == config.temboard.fromarg
    assert "ENVVAL" == config.temboard.fromenv
    assert "FILEVAL" == config.temboard.fromfile


def test_load_configparser():
    from temboardui.toolkit.configuration import iter_configparser_values
    from temboardui.toolkit.app import configparser

    parser = configparser.RawConfigParser()
    parser.add_section("section0")
    parser.set("section0", "option0", "pouet")

    values = list(iter_configparser_values(parser, "my.cfg"))

    assert 1 == len(values)
    assert "pouet" == values[0].value
    assert "section0_option0" == values[0].name
    assert "my.cfg" == values[0].origin


def test_pwd_denied(mocker):
    mod = "temboardui.toolkit.configuration"
    mocker.patch(mod + ".iter_configparser_values")
    cd = mocker.patch(mod + ".os.chdir")

    from temboardui.toolkit.configuration import MergedConfiguration

    config = MergedConfiguration()
    config.temboard = dict(configfile="pouet")

    cd.side_effect = [None, OSError()]
    config.load(parser=mocker.Mock(name="parser"), pwd="/etc/pouet")


def test_required():
    from temboardui.toolkit.configuration import (
        MergedConfiguration,
        OptionSpec,
        UserError,
        iter_defaults,
    )

    spec = OptionSpec("section", "req", default=OptionSpec.REQUIRED)
    config = MergedConfiguration(specs=[spec])
    assert not list(iter_defaults(config.specs))
    with pytest.raises(UserError):
        config.check_required()
