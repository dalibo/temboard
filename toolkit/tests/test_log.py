import logging


def test_color(mocker):
    from temboardtoolkit.log import ColoredStreamHandler

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
    from temboardtoolkit.log import MultilineFormatter

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


def test_systemd():
    from temboardtoolkit.log import SystemdFormatter

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
    from temboardtoolkit.log import LastnameFilter

    filter_ = LastnameFilter()
    filter_.root = "temboardtoolkit"

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

    record.name = "temboardtoolkit.titi"
    ret = filter_.filter(record)
    assert "titi" == record.lastname


def test_temboard_debug(mocker):
    mocker.patch("temboardtoolkit.log.sys.stderr.isatty")
    mocker.patch("temboardtoolkit.log.LastnameFilter.root", "temboardtoolkit")

    from temboardtoolkit.log import generate_logging_config

    config = generate_logging_config()
    assert "%(process)" not in config["formatters"]["console"]["format"]

    config = generate_logging_config(level="DEBUG", debug=False)

    assert "%(process)" in config["formatters"]["console"]["format"]
    assert "DEBUG" == config["loggers"]["temboardtoolkit"]["level"]

    config = generate_logging_config(level="INFO", debug=True)

    assert "%(process)" in config["formatters"]["console"]["format"]
    assert "DEBUG" == config["loggers"]["temboardtoolkit"]["level"]

    config = generate_logging_config(level="INFO", debug="__debug__")

    assert "%(process)" in config["formatters"]["console"]["format"]
    assert "DEBUG" == config["loggers"]["temboardtoolkit"]["level"]


def test_limit_debug(mocker):
    mocker.patch("temboardtoolkit.log.LastnameFilter.root", "temboardtoolkit")

    from temboardtoolkit.log import generate_logging_config

    config = generate_logging_config(
        level="INFO", debug="myplugins,temboardtoolkit.cli"
    )

    assert "INFO" == config["loggers"]["temboardtoolkit"]["level"]
    assert "DEBUG" == config["loggers"]["myplugins"]["level"]
    assert "DEBUG" == config["loggers"]["temboardtoolkit.cli"]["level"]


def test_setup(mocker):
    dc = mocker.patch("temboardtoolkit.log.dictConfig", autospec=True)
    from temboardtoolkit.log import setup_logging

    setup_logging()
    assert dc.called is True
