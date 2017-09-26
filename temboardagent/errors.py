class UserError(Exception):
    def __init__(self, message, retcode=1):
        super(UserError, self).__init__(message)
        self.retcode = retcode


class HTTPError(Exception):
    """ HTTP server errors """
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = {'error': str(message)}


class ConfigurationError(UserError):
    pass


class SharedItem_not_found(Exception):
    def __init__(self,):
        pass


class SharedItem_exists(Exception):
    def __init__(self,):
        pass


class SharedItem_bad_type_size(Exception):
    def __init__(self,):
        pass


class SharedItem_no_free_slot_left(Exception):
    def __init__(self,):
        pass


class NotificationError(Exception):
    """ Notification errors """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = str(message)
