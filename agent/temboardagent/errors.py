from .toolkit.errors import UserError

__all__ = ['UserError']


class NotificationError(Exception):
    """ Notification errors """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = str(message)
