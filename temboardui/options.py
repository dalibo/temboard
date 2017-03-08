from optparse import OptionParser


class CLIOptions(OptionParser):
    """
    Command line interface options parser.
    """
    def __init__(self, *args, **kwargs):
        OptionParser.__init__(self, *args, **kwargs)
        self.add_option(
            "-c", "--config", dest="configfile",
            help="Configuration file.", default="/etc/temboard/temboard.conf")


class temboarduiOptions(CLIOptions):
    """
    temboard options parser.
    """
    def __init__(self, *args, **kwargs):
        CLIOptions.__init__(self, *args, **kwargs)
        self.add_option(
            "-d", "--daemon", dest="daemon", action="store_true",
            help="Run in background.", default=False)
        self.add_option(
            "-p", "--pid-file", dest="pidfile",
            help="PID file.", default="/run/temboard.pid")
        self.add_option(
            "--debug",
            action="store_true", dest="debug", default=False,
            help="Debug mode for development.")
