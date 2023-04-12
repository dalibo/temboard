class CLIError(Exception):
    """ CLI errors """

    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = str(message)


class TemboardUIError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = int(code)
        self.message = str(message)
