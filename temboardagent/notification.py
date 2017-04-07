from temboardagent.queue import Queue, Message
from temboardagent.errors import NotificationError
import json
import datetime

"""
Notifications are messages stored in a Queue aimed to keep a track of each
possible action impacting PostgreSQL server configuration or behaviour.

For now, they are pushed when one of the following actions is triggered:
  * PostgreSQL reload, stop, start, restart.
  * Setting changes.
  * HBA file update.

Queue max size is set to 10MB, LIFO behaviour is expected.
"""


class Notification(object):

    def __init__(self, username, message, date=None):
        if date is None:
            self.date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        else:
            self.date = date
        self.username = username
        self.message = message


class NotificationMgmt():

    @classmethod
    def push(self, config, notification):
        try:
            # Notifications are stored in a "sliding" queue.
            q = Queue(file_path='%s/notifications.q' % (
                                config.temboard['home']),
                      max_size=10 * 1024 * 1024,  # 10MB
                      overflow_mode='slide')

            # Push the notification in the queue.
            q.push(Message(content=json.dumps({
                                        'date': notification.date,
                                        'username': notification.username,
                                        'message': notification.message})))
        except (Exception) as e:
            raise NotificationError('Can not push new notification: %s' %
                                    e.message)

    @classmethod
    def get_last_n(self, config, n):
        try:
            q_last = Queue(file_path='%s/notifications.q' % (
                                     config.temboard['home']),
                           max_length=10 * 1024 * 1024,
                           overflow_mode='slide')
            return q_last.get_last_n_messages(n)
        except (Exception) as e:
            raise NotificationError('Can not get last notifications: %s' %
                                    e.message)
