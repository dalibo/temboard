from multiprocessing import Lock
from multiprocessing.sharedctypes import Array
from ctypes import (Structure, c_char, c_double)
import time

from temboardagent.errors import (SharedItem_not_found, SharedItem_exists,
                                  SharedItem_bad_type_size,
                                  SharedItem_no_free_slot_left,
                                  NotificationError)
from temboardagent.types import T_SESSIONID_SIZE, T_USERNAME_SIZE
from temboardagent.notification import NotificationMgmt, Notification


class Session(Structure):
    """
    Session structure. The Session Array is shared by the HTTP server process
    and the scheduler process.
    """
    _fields_ = [
        # Session ID.
        ('sessionid', c_char * T_SESSIONID_SIZE),
        # Last update timestamp.
        ('time', c_double),
        # Username.
        ('username', c_char * T_USERNAME_SIZE)
    ]


class Sessions(object):
    """
    Sessions object.
    """
    def __init__(self, size=100):
        # Lock handler.
        self.lock = Lock()
        # Array size.
        self.size = size
        # Array of Session.
        self.sessions = Array(Session, self.size, lock=self.lock)

    def get_by_sessionid(self, sessionid):
        """
        Returns a Session by a sessionid.
        """
        for session in self.sessions:
            if session.sessionid == sessionid:
                return session
        raise SharedItem_not_found()

    def get_by_username(self, username):
        """
        Returns a Session by a username.
        """
        for session in self.sessions:
            if session.username == username:
                return session

    def add(self, session):
        """
        Add a new Session.
        """
        for i in range(0, self.size):
            if self.sessions[i].sessionid == session.sessionid:
                raise SharedItem_exists()
            if self.sessions[i].username == session.username:
                self.sessions[i] = Session()
        for i in range(0, self.size):
            if self.sessions[i].sessionid == b'':
                self.sessions[i] = session
                return
        raise SharedItem_no_free_slot_left()

    def update(self, session):
        """
        Modify a Session.
        """
        for i in range(0, self.size):
            if self.sessions[i].sessionid == session.sessionid:
                self.sessions[i] = session
                return
        raise SharedItem_not_found()

    def delete(self, sessionid):
        """
        Remove a Session.
        """
        for i in range(0, self.size):
            if self.sessions[i].sessionid == sessionid:
                self.sessions[i] = Session()
                return
        raise SharedItem_not_found()

    def add_tuple(self, t_session):
        """
        Convert to Session the given tuple and add it.
        """
        session = Session()
        if len(t_session) != len(session._fields_):
            raise SharedItem_bad_type_size()
        session.sessionid = t_session[0][:T_SESSIONID_SIZE]
        session.time = t_session[1]
        session.username = t_session[2][:T_USERNAME_SIZE]
        self.add(session)

    def purge_expired(self, ttl, logger, config):
        """
        Remove old Session when the Session last update time + TTL is prior to
         current timestamp.
        """
        for i in range(0, self.size):
            if len(self.sessions[i].sessionid) == T_SESSIONID_SIZE and \
               (self.sessions[i].time + ttl) < time.time():
                logger.info("Session with sessionid=%s expired." %
                            (self.sessions[i].sessionid))
                try:
                    NotificationMgmt.push(config, Notification(
                        username=self.sessions[i].username,
                        message="Session expired"))
                except NotificationError as e:
                    logger.error(e.message)

                self.sessions[i] = Session()
