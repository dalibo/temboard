from optparse import OptionParser

class CLIOptions(OptionParser):
    """
    Command line interface options parser.
    """
    def __init__(self, *args, **kwargs):
        OptionParser.__init__(self, *args, **kwargs)
        self.add_option("-c", "--config", dest="configfile",
            help="Configuration file.", default="/etc/temboard-agent/temboard-agent.conf")

class temboardOptions(CLIOptions):
    """
    temboard-agent options parser.
    """
    def __init__(self, *args, **kwargs):
        CLIOptions.__init__(self, *args, **kwargs)
        self.add_option("-d", "--daemon", dest="daemon", action="store_true",
            help="Run in background.", default=False)
        self.add_option("-p", "--pid-file", dest="pidfile",
            help="PID file.", default="/run/temboard-agent.pid")
