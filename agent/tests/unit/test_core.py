def test_version():
    from packaging.version import parse
    from temboardagent.version import __version__

    version = parse(__version__)

    assert "Version" == version.__class__.__name__
