class UserError(Exception):
    def __init__(self, message, retcode=1):
        super(UserError, self).__init__(message)
        self.retcode = retcode


class StorageEngineError(Exception):
    pass
