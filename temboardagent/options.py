from optparse import OptionParser


class CLIOptions(OptionParser):
    """
    Command line interface options parser.
    """
    def __init__(self, *args, **kwargs):
        OptionParser.__init__(self, *args, **kwargs)
        self.add_option("-c",
                        "--config",
                        dest="configfile",
                        help="Configuration file. Default: %default",
                        default="/etc/temboard-agent/temboard-agent.conf")


class temboardOptions(CLIOptions):
    """
    temboard-agent options parser.
    """
    def __init__(self, *args, **kwargs):
        CLIOptions.__init__(self, *args, **kwargs)
        self.add_option("-d",
                        "--daemon",
                        dest="daemon",
                        action="store_true",
                        help="Run in background. Default: %default",
                        default=False)
        self.add_option("-p",
                        "--pid-file",
                        dest="pidfile",
                        help="PID file. Default: %default",
                        default="/run/temboard-agent.pid")


class agentRegisterOptions(CLIOptions):
    """
    Command line interface options parser.
    """
    def __init__(self, *args, **kwargs):
        CLIOptions.__init__(self, *args, **kwargs)
        self.add_option("-h",
                        "--host",
                        dest="host",
                        help="Agent address. Default: %default",
                        default="localhost")
        self.add_option("-p",
                        "--port",
                        dest="port",
                        help="Agent listening TCP port. Default: %default",
                        default="2345")
        self.add_option("-g",
                        "--groups",
                        dest="groups",
                        help="Instance groups list, comma separated. "
                             "Default: %default",
                        default=None)
        self.add_option("--help",
                        dest="help",
                        action="store_true",
                        help="Show this help message and exit.",
                        default=False)
