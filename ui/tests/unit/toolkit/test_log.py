import logging


def test_color(mocker):
    from temboardui.toolkit.log import ColoredStreamHandler

    handler = ColoredStreamHandler()
    record = logging.getLogger().makeRecord(
        name="toto",
        level=logging.DEBUG,
        fn="toto.py",
        lno=42,
        msg="Message",
        args=(),
        exc_info=None,
    )
    s = handler.format(record)
    assert "\033[0m" in s
    assert "Message" in s


def test_multiline(mocker):
    from temboardui.toolkit.log import MultilineFormatter

    formatter = MultilineFormatter("PREFIX: %(message)s")
    record = logging.getLogger().makeRecord(
        name="toto",
        level=logging.DEBUG,
        fn="toto.py",
        lno=42,
        msg="Line1\nLine2",
        args=(),
        exc_info=None,
    )
    s = formatter.format(record)

    assert "PREFIX: Line1" in s
    assert "\tLine2" in s

    record.msg = "Single"
    s = formatter.format(record)
    assert "PREFIX: Single" in s


def test_systemd(mocker):
    from temboardui.toolkit.log import SystemdFormatter

    formatter = SystemdFormatter("PREFIX: %(message)s")
    record = logging.getLogger().makeRecord(
        name="toto",
        level=logging.DEBUG,
        fn="toto.py",
        lno=42,
        msg="Line1\nLine2",
        args=(),
        exc_info=None,
    )
    s = formatter.format(record)
    assert s.startswith("<7>PREFIX")


def test_lastname():
    from temboardui.toolkit.log import LastnameFilter

    filter_ = LastnameFilter()
    record = logging.getLogger().makeRecord(
        name="toto",
        level=logging.DEBUG,
        fn="toto.py",
        lno=42,
        msg="Message",
        args=(),
        exc_info=None,
    )
    ret = filter_.filter(record)
    assert ret
    assert "toto" == record.lastname

    record.name = "temboardui.titi"
    ret = filter_.filter(record)
    assert "titi" == record.lastname


def test_temboard_debug(mocker):
    mocker.patch("temboardui.toolkit.log.sys.stderr.isatty")

    from temboardui.toolkit.log import generate_logging_config

    config = generate_logging_config()
    assert "%(process)" not in config["formatters"]["console"]["format"]

    config = generate_logging_config(level="DEBUG", debug=False)

    assert "%(process)" in config["formatters"]["console"]["format"]
    assert "DEBUG" == config["loggers"]["temboardui"]["level"]

    config = generate_logging_config(level="INFO", debug=True)

    assert "%(process)" in config["formatters"]["console"]["format"]
    assert "DEBUG" == config["loggers"]["temboardui"]["level"]

    config = generate_logging_config(level="INFO", debug="__debug__")

    assert "%(process)" in config["formatters"]["console"]["format"]
    assert "DEBUG" == config["loggers"]["temboardui"]["level"]


def test_limit_debug():
    from temboardui.toolkit.log import generate_logging_config

    config = generate_logging_config(level="INFO", debug="myplugins,temboardui.cli")

    assert "INFO" == config["loggers"]["temboardui"]["level"]
    assert "DEBUG" == config["loggers"]["myplugins"]["level"]
    assert "DEBUG" == config["loggers"]["temboardui.cli"]["level"]


def test_setup(mocker):
    dc = mocker.patch("temboardui.toolkit.log.dictConfig", autospec=True)
    from temboardui.toolkit.log import setup_logging

    setup_logging()
    assert dc.called is True
