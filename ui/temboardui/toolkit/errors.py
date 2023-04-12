class TemboardError(Exception):
    """An internal temBoard error."""


class UserError(Exception):
    def __init__(self, message, retcode=1):
        super().__init__(message)
        self.retcode = retcode


class StorageEngineError(Exception):
    pass
