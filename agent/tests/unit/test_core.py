def test_version():
    from pkg_resources import parse_version
    from temboardagent.version import __version__

    version = parse_version(__version__)

    assert "Version" == version.__class__.__name__
