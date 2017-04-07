from multiprocessing import Lock
from multiprocessing.sharedctypes import Array
from ctypes import (Structure, c_char, c_double, c_int, c_wchar,
                    c_short)
import os
import time

from temboardagent.errors import (SharedItem_not_found, SharedItem_exists,
                                  SharedItem_bad_type_size,
                                  SharedItem_no_free_slot_left,
                                  NotificationError)
from temboardagent.types import (T_COMMANDID_SIZE, T_WORKER_SIZE,
                                 T_PARAMETERS_SIZE, T_RESULT_SIZE,
                                 T_SESSIONID_SIZE, T_USERNAME_SIZE)
from temboardagent.workers import COMMAND_START, COMMAND_DONE, COMMAND_ERROR
from temboardagent.notification import NotificationMgmt, Notification


class Command(Structure):
    """
    Command structure based on ctypes for sharedctypes' Array compatibility
    which is the only way for getting an array of structurized elements in a
    shared memory segment.
    Comands are keeped in a shared memory segment because they have to be
    accessed by:
        - HTTP server process when it needs to ensure the unicity. ie: we
          don't want to get the same command running twice at the same time.
          The other case is for GET /command/<cid> API.
        - scheduler process for the cleaning task.
        - worker process itself when it needs to update command status.
    """
    _fields_ = [
        # Command ID.
        ('commandid', c_char * T_COMMANDID_SIZE),
        # Last update timestamp.
        ('time', c_double),
        # Worker's pid.
        ('pid', c_int),
        # Worker name.
        ('worker', c_char * T_WORKER_SIZE),
        # Parameters (serialized).
        ('parameters', c_wchar * T_PARAMETERS_SIZE),
        # Command state.
        ('state', c_short),
        # Command return.
        ('result', c_wchar * T_RESULT_SIZE)
    ]


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


class Commands(object):
    """
    Commands object.
    """
    def __init__(self, size=100):
        # Lock handler.
        self.lock = Lock()
        # Array size.
        self.size = size
        # Array of Command.
        self.commands = Array(Command, self.size, lock=self.lock)

    def get_by_commandid(self, commandid):
        """
        Load a Command by commandid.
        """
        for command in self.commands:
            if command.commandid == commandid:
                return command
        raise SharedItem_not_found()

    def add(self, command):
        """
        Add a new Command in the shared array.
        """
        for i in range(0, self.size):
            if self.commands[i].commandid == command.commandid:
                raise SharedItem_exists()
        for i in range(0, self.size):
            if self.commands[i].commandid == b'':
                self.commands[i] = command
                return
        raise SharedItem_no_free_slot_left()

    def update(self, command):
        """
        Modify a Command in the shared array.
        """
        for i in range(0, self.size):
            if self.commands[i].commandid == command.commandid:
                self.commands[i] = command
                return
        raise SharedItem_not_found()

    def delete(self, commandid):
        """
        Remove a Command from the shared array.
        """
        for i in range(0, self.size):
            if self.commands[i].commandid == commandid:
                self.commands[i] = Command()
                return
        raise SharedItem_not_found()

    def add_tuple(self, t_command):
        """
        Convert the incoming tuple (t_command) as a Command and add it in the
        shared array.
        """
        command = Command()
        if len(t_command) != len(command._fields_):
            raise SharedItem_bad_type_size()
        command.commandid = t_command[0][:T_COMMANDID_SIZE]
        command.time = t_command[1]
        command.pid = t_command[2]
        command.worker = t_command[3][:T_WORKER_SIZE]
        command.parameters = t_command[4][:T_PARAMETERS_SIZE]
        command.state = t_command[5]
        command.result = t_command[6][:T_RESULT_SIZE]
        self.add(command)

    def purge_expired(self, ttl, logger):
        """
        In charge of removing old Commands (when Command's last update time +
        given TTL is prior to current timestamp and the worker finished its
        work on it) from the shared array.
        """
        for i in range(0, self.size):
            if len(self.commands[i].commandid) == T_COMMANDID_SIZE and \
                (self.commands[i].time + ttl) < time.time() and \
                (self.commands[i].state == COMMAND_DONE or
                    self.commands[i].state == COMMAND_ERROR):
                logger.debug("Removing command with commandid=%s" %
                             (self.commands[i].commandid))
                # Deletion: overwrite array element by a null Command.
                self.commands[i] = Command()
            # We need to ckeck if the processes executing commands with a
            # state = COMMAND_START are stil alive and then remove the
            # command if they are not.
            if len(self.commands[i].commandid) == T_COMMANDID_SIZE and \
               self.commands[i].state == COMMAND_START and \
               self.commands[i].pid > 0:
                try:
                    os.getpgid(self.commands[i].pid)
                except OSError:
                    logger.debug("Removing command with commandid=%s." % (
                                 self.commands[i].commandid))
                    self.commands[i] = Command()

    def check_uniqueness(self, worker, parameters):
        """
        Verify that there is no other identic command in progress.
        """
        for i in range(0, self.size):
            if len(self.commands[i].commandid) == T_COMMANDID_SIZE and \
               self.commands[i].worker == worker and \
               self.commands[i].parameters == parameters and \
               self.commands[i].state != COMMAND_DONE and \
               self.commands[i].state != COMMAND_ERROR:
                raise SharedItem_exists()


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
