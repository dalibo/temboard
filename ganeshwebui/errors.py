class CLIError(Exception):
    """ CLI errors """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = str(message)

class ConfigurationError(Exception):
    """ Configuration errors """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = str(message)
