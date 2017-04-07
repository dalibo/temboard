import fcntl
import os
import time
import hashlib
import json


class Message(object):

    def __init__(self, id=-1, sign=None, content=''):
        if id == -1:
            self.id = int(time.time() * 1000000)
        else:
            self.id = id
        if sign is None:
            self.sign = hashlib.md5(content.encode('utf-8')).hexdigest()[0:9]
        else:
            self.sign = sign
        self.content = content

    def serialize(self,):
        return "%s:%s:%s\n" % (str(self.id), self.sign, self.content)


class Queue(object):
    """On disk queueing system."""

    def __init__(self, file_path, max_size=-1, max_length=-1,
                 overflow_mode='slide'):
        """
        Constructor

        file_path: queue file path
        max_size: maximum queue size (bytes), default -1: no limit
        max_length: maximum queue length, default -1: no limit
        overflow_mode: behaviour to have when queue size or length exceed the
                       max value on a push(), available values are:
                       - 'slide': the oldest message is removed and the new
                       one pushed.
                       - 'drop': the new message is dropped.
        """
        self.file_path = file_path
        self.max_size = max_size
        if self.max_size == -1:
            self.max_length = max_length
        else:
            self.max_length = -1
        self.overflow_mode = overflow_mode

    def get_length(self,):
        """ Read the whole queue file and return the number of lines. """
        try:
            with open(self.file_path, 'r') as fd:
                fcntl.flock(fd, fcntl.LOCK_SH)
                n = 0
                for _ in fd.readlines():
                    n += 1
                fcntl.flock(fd, fcntl.LOCK_UN)
                return n
        except Exception:
            return 0

    def get_last_message(self):
        return list(self.get_last_n_messages(1))[0]

    def get_last_n_messages(self, n):
        """
        Generator intended to return the last n messages from the queue.
        As far as the last records are located at the end of the file, we read
        the file backwards until the number of desired lines is reached or the
        whole file has been read. -1 means no limit.
        """
        buf_size = 8192
        try:
            with open(self.file_path, 'r') as fd:
                fcntl.flock(fd, fcntl.LOCK_SH)
                segment = None
                offset = 0
                n_line = 0
                # Move to the EOF
                fd.seek(0, os.SEEK_END)
                # Get file size using tell()
                file_size = total_size = remaining_size = fd.tell()

                while (remaining_size > 0):
                    offset = min(total_size, offset + buf_size)
                    # Move pointer to the next position.
                    fd.seek(file_size - offset)
                    # Read a chunk into the buffer.
                    buffer = fd.read(min(remaining_size, buf_size))
                    remaining_size -= buf_size
                    # Split buffer content by EOL.
                    lines = buffer.split('\n')

                    if segment is not None:
                        # Case when we need to concatenate the first uncomplete
                        # line of the last loop iter. with the last one of this
                        # current iteration.
                        if buffer[-1] is not '\n':
                            lines[-1] += segment
                        else:
                            n_line += 1
                            if (n > -1 and n_line > n):
                                fcntl.flock(fd, fcntl.LOCK_UN)
                                break
                            yield json.loads(
                                    self.parse_row_message(segment).content)
                    segment = lines[0]
                    # Read each line.
                    for idx in range(len(lines) - 1, 0, -1):
                        if len(lines[idx]):
                            n_line += 1
                            if (n > -1 and n_line > n):
                                fcntl.flock(fd, fcntl.LOCK_UN)
                                break
                            yield json.loads(
                                    self.parse_row_message(lines[idx]).content)

                if segment is not None:
                    yield json.loads(self.parse_row_message(segment).content)
                fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            return

    def get_content_all_messages(self):
        """
        Get all messages
        """
        try:
            buffers = list()
            with open(self.file_path, 'r') as fd:
                fcntl.flock(fd, fcntl.LOCK_SH)
                for row_msg in fd.readlines():
                    try:
                        msg = self.parse_row_message(row_msg)
                        buffers.append(json.loads(msg.content))
                    except Exception:
                        pass
                fcntl.flock(fd, fcntl.LOCK_UN)
            return buffers
        except Exception:
            return

    def get_size(self):
        """ Return queue file size. """
        try:
            with open(self.file_path, 'r') as fd:
                fcntl.flock(fd, fcntl.LOCK_SH)
                size = os.fstat(fd.fileno()).st_size
                fcntl.flock(fd, fcntl.LOCK_UN)
                return size
        except Exception:
            return 0

    def push(self, message):
        """ Push a new message. """
        if self.overflow_mode == 'drop':
            if self.max_length > -1 and self.get_length() >= self.max_length:
                return
            if self.max_size > -1 and self.get_size() >= self.max_size:
                return

        with open(self.file_path, 'a') as fd:
            # Let's hold an exclusive lock.
            fcntl.flock(fd, fcntl.LOCK_EX)
            fd.write(message.serialize())
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

        if self.overflow_mode == 'slide':
            if self.max_size == -1 and self.max_length > -1:
                while self.get_length() > self.max_length:
                    self.shift()
            elif self.max_size > -1 and self.max_length == -1:
                while self.get_size() > self.max_size:
                    self.shift()

    def parse_row_message(self, row_message):
        if row_message:
            (id, sign) = row_message[:26].split(":")
            content = row_message[27:]
            return Message(id, sign, content.strip())
        else:
            return

    def shift(self, delete=True, check_msg=None):
        """ Get and remove from the queue the oldest message. """
        try:
            with open(self.file_path, 'r+') as fd:
                fcntl.flock(fd, fcntl.LOCK_EX)
                i = 0
                row_message = None
                message = None
                for line in fd.readlines():
                    if i == 0:
                        row_message = line
                        message = self.parse_row_message(row_message)
                        if delete is False:
                            fcntl.flock(fd, fcntl.LOCK_UN)
                            return message
                        if type(check_msg) is Message:
                            if not (message.id == check_msg.id and
                                    message.sign == check_msg.sign):
                                fcntl.flock(fd, fcntl.LOCK_UN)
                                return message
                        # Go back to the first line.
                        fd.seek(0)
                    else:
                        fd.write(line)
                    i += 1
                fd.truncate()
                fcntl.flock(fd, fcntl.LOCK_UN)
                fd.close()
                return message
        except IOError:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception:
                pass
            pass


def purge_queue_dir(queue_dir, exceptions=[]):
    """
    Remove queue files
    """
    if os.path.exists(queue_dir):
        for filename in os.listdir(queue_dir):
            if filename.endswith(".q") and filename not in exceptions:
                os.remove("%s/%s" % (queue_dir, filename))
