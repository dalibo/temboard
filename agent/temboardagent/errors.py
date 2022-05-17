from .toolkit.errors import UserError

__all__ = ['UserError']


class ConfigurationError(UserError):
    pass


class HTTPError(Exception):
    """ HTTP server errors """
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = {'error': str(message)}


class NotificationError(Exception):
    """ Notification errors """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = str(message)
