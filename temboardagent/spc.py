"""
Simple PostgreSQL Connector module.
author: Julien Tachoires <julien.tachoires@dalibo.com>
"""

import socket
import ssl
import hashlib
import struct
import re
from io import BytesIO
import datetime
import codecs


class perror(Exception):
    """
    Protocol Error.
    """
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message


class error(Exception):
    """
    Connector Error.
    """
    def __init__(self, code, typ, message):
        Exception.__init__(self, message)
        self.code = code
        self.typ = typ
        self.message = message


def get_pgpass(pgpass=None):
    """
    Get postgres' password using pgpass file.

    http://www.postgresql.org/docs/9.2/static/libpq-pgpass.html
    http://wiki.postgresql.org/wiki/Pgpass
    """
    if pgpass is None:
        from os.path import expanduser
        home = expanduser("~")
        pgpass = "{0}/.pgpass".format(str(home))
    ret = []
    with open(pgpass, 'r') as filep:
        content = filep.readlines()
        for line in content:
            res = None
            res = re.match(r"^([^:]+):([^:]+):([^:]+):([^:]+):(.*)$", line)
            if res is not None:
                ret.append(res.group(1, 2, 3, 4, 5))
        return ret
    raise Exception("pgpass file not found")


def pg_escape(in_string, escapee_char=r"'"):
    out_string = ''
    out_string += escapee_char
    out_string += re.sub(escapee_char, escapee_char * 2, in_string)
    out_string += escapee_char
    return out_string


class protocol3(object):
    """
    PostgreSQL FE/BE protocol 3.0 implementation.
    """
    _version = 196608
    _ssl_code = 80877103

    def __init__(self, encoding='UTF-8'):
        # Client encoding
        self._encoding = encoding
        # Response parsers mapping
        self._response_parsers = {
            b'R': 'parse_authentication_response',
            b'S': 'parse_parameter_status',
            b'K': 'parse_backend_key_data',
            b'Z': 'parse_ready_for_query',
            b'E': 'parse_error',
            b'T': 'parse_row_description',
            b'D': 'parse_data_row',
            b'C': 'parse_command_complete',
            b'H': 'parse_copy_out_response',
            b'd': 'parse_copy_data',
            b'c': 'parse_copy_done',
            b'N': 'parse_notice',
            b'W': 'parse_copy_both_response',
            # Not implemented
            b'A': 'ignore',  # Notification
            b'n': 'ignore',  # No Data
            b'I': 'ignore',  # Empty query
        }

    def set_encoding(self, encoding):
        self._encoding = encoding

    def ssl_request(self,):
        """
        SSLRequest for SSL negociation.
        """
        return struct.pack('!L', 8) + struct.pack('!L', self._ssl_code)

    def startup(self, user, database='', replication=False):
        """
        Startup packet.
        """
        data = struct.pack('!L', self._version) + b'user' + b'\x00' \
            + user.encode(self._encoding) + b'\x00' + b'database' + b'\x00' \
            + database.encode(self._encoding)
        if replication:
            data += b'\x00replication\x001'
        data += b'\x00\x00'
        return struct.pack('!L', len(data) + 4) + data

    def terminate(self,):
        """
        End of session.
        """
        return b'X' + struct.pack('!L', 4)

    def password_message(self, password):
        """
        PasswordMessage packet.
        """
        data = password.encode(self._encoding) + b'\x00'
        return b'p' + struct.pack('!L', len(data) + 4) + data

    def query(self, query):
        """
        Simple query mode.
        """
        data = query.encode(self._encoding) + b'\x00'
        return b'Q' + struct.pack('!L', len(data) + 4) + data

    def copy_data(self, sdata):
        data = b'd' + struct.pack('!L', len(sdata) + 4) + sdata
        return data

    def ignore(self, data):
        """
        Dummy parser for not implemented responses.
        """
        return (data[0:1], None)

    def _check_message_length(self, message, length):
        """
        Verify real message length.
        """
        if length != len(message) - 1:
            raise perror("Unvalid response length.")

    def parse_ssl_response(self, data):
        """
        Parse responses for SSL negotiation.
        Returns True if the postgresql backend accepts SSL.
        """
        if len(data) != 1:
            raise perror("Bad SSLRequest response")
        if data.decode(self._encoding) == 'S':
            return True
        return False

    def parse_message(self, data):
        """
        Wrapper around responses parsers.
        """
        if len(data) == 0:
            raise perror("Response is empty")
        return getattr(self, self._response_parsers[data[0:1]])(data)

    def parse_notice(self, data):
        """
        NoticeResponse parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        ret = []
        if length > 6:
            for raw in data[5:].split(b'\x00'):
                if len(raw) == 0:
                    continue
                code = struct.unpack('!c', raw[0:1])[0]
                string = raw[1:].decode(self._encoding)
                ret.append((code, string))
        return (data[0:1], ret)

    def parse_authentication_response(self, data):
        """
        Authentication response parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        code = struct.unpack('!L', data[5:9])[0]
        extra = {}
        extra['code'] = code
        if code == 5:
            extra['salt'] = struct.unpack('!4s', data[9:13])[0]
        return (data[0:1], extra)

    def parse_parameter_status(self, data):
        """
        ParameterStatus response parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        i = 0
        extra = {}
        for val in data[5:].split(b'\x00'):
            if (i % 2) == 0:
                key = val.decode(self._encoding)
            else:
                extra[key] = val.decode(self._encoding)
            i += 1
        return (data[0:1], extra)

    def parse_backend_key_data(self, data):
        """
        BackendKeyData response parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        extra = {
            'pid': struct.unpack('!L', data[5:9])[0],
            'key': struct.unpack('!L', data[9:13])[0]
        }
        return (data[0:1], extra)

    def parse_ready_for_query(self, data):
        """
        ReadyForQuery response parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        extra = {
            'status': data[5:6].decode(self._encoding)
        }
        return (data[0:1], extra)

    def parse_error(self, data):
        """
        Error parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        if length == 4:
            return (data[0], None)
        typ = data[5:6].decode(self._encoding)
        string = data[6:]
        return (data[0:1], {'type': typ, 'string': string})

    def parse_row_description(self, data):
        """
        RowDescription parser.
        """
        (length, nb_fields) = struct.unpack('!LH', data[1:7])
        self._check_message_length(data, length)
        ndata = data[7:]
        ret = []
        if nb_fields > 0:
            pos = 0
            while pos < nb_fields:
                eop = ndata.index(b'\x00')
                name = ndata[0:eop].decode(self._encoding)
                ndata = ndata[eop + 1:]
                (table_oid, col_oid, type_oid, type_size, typmod, format_code)\
                    = struct.unpack('!LhLhlh', ndata[0:18])
                ndata = ndata[18:]
                ret.append({
                    'name': name,
                    'table_oid': table_oid,
                    'col_oid': col_oid,
                    'type_oid': type_oid,
                    'type_size': type_size,
                    'typmod': typmod,
                    'format_code': format_code
                })
                pos += 1
        return (data[0:1], ret)

    def parse_data_row(self, data):
        """
        DataRow parser.
        """
        (length, nb_fields) = struct.unpack('!LH', data[1:7])
        self._check_message_length(data, length)
        ret = []
        if nb_fields > 0:
            pos = 0
            cur = 7
            while pos < nb_fields:
                col_length = struct.unpack('!l', data[cur:cur + 4])[0]
                cur += 4
                if col_length > 0:
                    value = data[cur:cur + col_length].decode(self._encoding)
                    cur += col_length
                else:
                    value = None
                ret.append(value)
                pos += 1
        return (data[0:1], ret)

    def parse_command_complete(self, data):
        """
        CommandComplete parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        body = data[5:].decode(self._encoding)
        ret = {}
        if body[0:6] == 'INSERT':
            res = re.match('^INSERT ([0-9]+) ([0-9]+)', body)
            if res is None:
                raise perror("Unvalid CommandComplete message.")
            ret = {
                'command': 'INSERT',
                'oid_table': res.group(1),
                'nb_rows': int(res.group(2))
            }
        else:
            res = re.match('^([A-Z]+) ([0-9]+)', body)
            if res is not None:
                ret = {'command': res.group(1), 'nb_rows': int(res.group(2))}
            else:
                ret = {'command': body[0:-1], 'nb_rows': 0}
        return (data[0:1], ret)

    def parse_copy_out_response(self, data):
        """
        CopyOutResponse parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        n_col = struct.unpack('!H', data[6:8])[0]
        ret = []
        pos = 0
        ndata = data[8:]
        while pos < n_col:
            ret.append(struct.unpack('!H', ndata[0:2])[0])
            ndata = ndata[2:]
            pos += 1
        return (data[0:1], ret)

    def parse_copy_data(self, data):
        """
        CopyData parser.
        """
        length = struct.unpack('!L', data[1:5])[0]
        self._check_message_length(data, length)
        body = data[5:]
        return (data[0:1], body)

    def parse_copy_done(self, data):
        return (data[0:1], None)

    def parse_copy_both_response(self, data):
        return self.parse_copy_out_response(data)

    def is_error(self, typ):
        """
        Is an error message ?
        """
        return typ == b'E'

    def is_auth_md5(self, message):
        """
        Is MD5 authentication required ?
        """
        return message[0][0:1] == b'R' and message[1]['code'] == 5

    def is_auth_cleartext(self, message):
        """
        Is cleartext authentication required ?
        """
        return message[0][0:1] == b'R' and message[1]['code'] == 3

    def is_auth_ok(self, message):
        """
        Is authentication done ?
        """
        return message[0][0:1] == b'R' and message[1]['code'] == 0

    def is_auth_supported(self, message):
        """
        Is the authentication method implemented ?
        """
        return message[0][0:1] == b'R' and (
            message[1]['code'] == 3 or
            message[1]['code'] == 5 or
            message[1]['code'] == 0)

    def is_parameter_status(self, typ):
        """
        Is a ParameterStatus message ?
        """
        return typ == b'S'

    def is_ready_for_query(self, typ):
        """
        Is a ReadyForQuery message ?
        """
        return typ == b'Z'

    def is_backend_key_data(self, typ):
        """
        Is a BackendKeyData message ?
        """
        return typ == b'K'

    def is_data_row(self, typ):
        """
        Is a DataRow message ?
        """
        return typ == b'D'

    def is_row_description(self, typ):
        """
        Is a RowDescription message ?
        """
        return typ == b'T'

    def is_command_complete(self, typ):
        """
        Is a CommandComplete message ?
        """
        return typ == b'C'

    def is_empty_query_response(self, typ):
        """
        Is an EmptyQueryResponse message ?
        """
        return typ == b'I'

    def is_copy_out_response(self, typ):
        """
        Is a CopyOutResponse message ?
        """
        return typ == b'H'

    def is_copy_data(self, typ):
        """
        Is a CopyData message ?
        """
        return typ == b'd'

    def is_copy_done(self, typ):
        """
        Is a CopyDone message ?
        """
        return typ == b'c'

    def get_salt(self, message):
        """
        Get salt value from the first authentication message
        (parsed) while dealing with MD5 method.
        """
        return message[1]['salt']

    def get_eop_tags(self,):
        """
        Return a tag list corresponding to messages:
        Error, NoData, ReadyForQuery, AuthResponse, EmptyQueryResponse
        """
        return [b'n', b'I', b'E', b'Z', b'R']


class message_buffer(object):
    """
    Message buffer class.
    """
    def __init__(self,):
        self._bio = BytesIO()
        self._pos = 0

    def write(self, data):
        """
        Write data at the end of the buffer.
        """
        self._bio.seek(0, 2)
        self._bio.write(data)

    def truncate(self,):
        """
        Truncate the buffer.
        """
        self._bio.truncate(0)
        self._bio.seek(0)
        self._pos = 0

    def get_messages(self,):
        """
        Fetch messages with a generator.
        """
        pos = 0
        # Need to know the buffer length.
        self._bio.seek(0, 2)
        buf_len = self._bio.tell()
        # If empty, nothing to do.
        if buf_len == 0:
            raise StopIteration

        self._bio.seek(pos)
        while pos < buf_len:
            # Read message header: the first 5 bytes
            header = self._bio.read(5)
            if len(header) < 5:
                raise perror("Unvalid message from buffer")
            # Get message length from the header.
            length = struct.unpack('!L', header[1:5])[0]
            pos += length + 1
            if pos > buf_len:
                raise perror("Unvalid message from buffer")
            body = self._bio.read(length - 4)
            yield header + body

    def get_messages_stream(self,):
        """
        Fetch messages with a generator and stop iteration when the last
        message is not complete. This method has to be used when we don't
        want to bufferize all messages received before parsing them.
        """
        pos_eom = 0
        # Need to know the buffer length.
        self._bio.seek(0, 2)
        buf_len = self._bio.tell()
        if buf_len == 0:
            raise StopIteration

        self._bio.seek(0)
        while pos_eom < buf_len:
            # Read message header: the first 5 bytes
            header = self._bio.read(5)
            if len(header) < 5:
                self.truncate()
                self.write(header)
                raise StopIteration
            # Get message length from the header.
            length = struct.unpack('!L', header[1:5])[0]
            pos_eom += length + 1
            if pos_eom > buf_len:
                body = self._bio.read(buf_len - self._bio.tell())
                self.truncate()
                self.write(header + body)
                raise StopIteration
            body = self._bio.read(length - 4)
            yield header + body
        if pos_eom == buf_len:
            self.truncate()

    def is_eop(self, eop_msg_tags):
        """
        Will walk through the message buffer and looking for an EOP
        (End Of Packet) message.
        """
        pos = self._pos
        self._bio.seek(0, 2)
        buf_len = self._bio.tell()
        if buf_len == 0:
            return False
        while pos < buf_len:
            self._bio.seek(pos)
            header = self._bio.read(5)
            if len(header) < 5:
                return False
            length = struct.unpack('!L', header[1:5])[0]
            pos += length + 1
            if pos > buf_len:
                return False
            else:
                self._pos = pos
            if header[0:1] in eop_msg_tags:
                return True
        return False


class connector(object):
    """
    PostgreSQL connector class.
    """

    def __init__(
            self,
            host,
            port,
            user,
            password='',
            database='',
            use_ssl=True):
        # Connection parameters.
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._ssl = use_ssl
        # IPv4 host address.
        self._host_ip4 = None
        # IPv6 host address.
        self._host_ip6 = None
        # Unix socket path.
        self._host_unix = None
        # Socket.
        self._socket = None
        # protocol3 instance.
        self._protocol = protocol3()
        # message_buffer instance.
        self._message_buffer = message_buffer()
        # Size in bytes to read at each socket.recv() call.
        self._socket_read_length = 2048
        # Is the authentication phase done ?
        self._is_auth = False
        # Is the backend ready for query ?
        self._is_backend_ready = False
        # Backend key.
        self._backend_key = None
        # Backend PID.
        self._backend_pid = None
        # Some values sent by the backend.
        self._parameter_status = {}
        # Current query.
        self._query = ''
        # Rows (if any) returned.
        self._rows = []
        # Number of rows affected by the query.
        self._nb_rows = None
        # Socket default timeout.
        self._default_timeout = 60  # Seconds
        # PostgreSQL version
        self._pg_version = 0
        # replication
        self._replication = False
        # client encoding
        self._encoding = 'UTF-8'

    def _set_ip_type(self,):
        """
        Convert the given hostname into a more convenient form.
        """
        # ip4
        if re.match(r'(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)'  # noqa W605
                    r'(\.(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)){3}$',
                    self._host):
            self._host_ip4 = self._host
        # ip6
        elif re.match(r'^[0-9a-fA-F]+:([0-9a-fA-F]*:*){0,6}:[0-9a-fA-F]+$',
                      self._host):
            self._host_ip6 = self._host
        # unix socket
        elif re.match(r'^\/.*', self._host):
            self._host_unix = self._host
        # hostname
        else:
            try:
                for addr in socket.getaddrinfo(self._host,
                                               self._port,
                                               socket.AF_UNSPEC,
                                               socket.SOCK_STREAM):
                    if addr[0] == socket.AF_INET:
                        self._host_ip4 = addr[4][0]
                    if addr[0] == socket.AF_INET6:
                        self._host_ip6 = addr[4][0]
            except socket.gaierror:
                raise error('PGC404', 'FATAL', "Unknown name or service"
                            " '{host}'".format(host=self._host))

    def _socket_read(self,):
        """
        Read (from the socket), write (into the buffer)
        """
        self._message_buffer.truncate()
        while not self._message_buffer.is_eop(self._protocol.get_eop_tags()):
            try:
                raw_data = self._socket.recv(self._socket_read_length)
            except socket.timeout:
                raise error('PGC105', 'FATAL', "Timeout")
            except socket.error as err:
                raise error('PGC106', 'FATAL',
                            "Socket error: {msg}".format(msg=err))
            self._message_buffer.write(raw_data)

    def _get_messages(self, method):
        """
        Read and parse messages from the buffer.
        """
        for raw in method():
            try:
                yield self._protocol.parse_message(raw)
            except perror as err:
                raise error('PGC107', 'FATAL', "Protocol violation: "
                                               "{msg}".format(msg=err.message))

    def _check_message_error(self, message):
        """
        Raise an error if the message is an error coming from the backend.
        """
        if self._protocol.is_error(message[0]):
            code = 'PGC200'
            typ = 'FATAL'
            msg = 'PostgreSQL backend error.'
            if message[1] is not None:
                err_string = message[1]['string']
                err_split = err_string.split(b'\x00')
                msg = err_split[3][1:].decode(self._encoding)
                typ = err_split[0][0:].decode(self._encoding)
                code = err_split[2][1:].decode(self._encoding)

            raise error(code, typ, msg)

    def _create_new_socket(self,):
        """
        Create a new socket.
        """
        tmp_socket = None
        # Convert "host" parameter to a valid socket address
        self._set_ip_type()
        if self._host_unix is None \
                and self._host_ip4 is None \
                and self._host_ip6 is None:
            raise error('PGC101', 'FATAL', "Could not connect to "
                                           "{host}".format(host=self._host))

        # Try with Unix socket
        if self._host_unix is not None:
            try:
                tmp_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                tmp_socket.connect(self._host_unix + '/.s.PGSQL.' +
                                   str(self._port))
                return tmp_socket
            except socket.error:
                raise error('PGC101', 'FATAL', "Could not connect to "
                                               "{host}".format(
                                                   host=self._host_unix))
        # Try with IPV4
        if self._host_ip4 is not None:
            try:
                tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tmp_socket.connect((self._host_ip4, self._port))
                return tmp_socket
            except socket.error:
                if self._host_ip6 is None:
                    raise error('PGC101', 'FATAL',
                                "Could not connect to {host}".format(
                                    host=self._host_ip4))

        # Try with IPV6
        if self._host_ip6 is not None:
            try:
                tmp_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                tmp_socket.connect((self._host_ip6, self._port))
                return tmp_socket
            except socket.error:
                raise error('PGC101', 'FATAL', "Could not connect to "
                                               "{host}".format(
                                                   host=self._host_ip6))

    def _socket_send(self, data):
        """
        Write data through the socket.
        """
        length = self._socket.send(data)
        if length != len(data):
            raise error('PGC106', 'FATAL', "Could not send all data.")

    def _wrap_ssl_socket(self, tmp_socket,):
        """
        Wrap the socket with SSL layer.
        """
        if self._ssl is True:
            data = self._protocol.ssl_request()
            tmp_socket.send(data)
            res = tmp_socket.recv(self._socket_read_length)
            if self._protocol.is_error(res[0]):
                raise error('PGC103', 'FATAL', "SSL error")
            if self._protocol.parse_ssl_response(res):
                self._socket = ssl.wrap_socket(tmp_socket)
            else:
                self._socket = tmp_socket
        else:
            self._socket = tmp_socket

    def _set_parameter_status(self, key, value):
        """
        Write a key,value pair returned in ParameterStatus message
        into self._parameter_status dict.
        """
        self._parameter_status[key] = value
        version = ''
        if key == 'server_version':
            # First remove anything after any potential space
            value = value.split(' ')[0]
            for num in value.split('.'):
                snum = ''
                num = re.sub(r"devel|beta|rc", "", str(num))
                num = re.sub(r"^(\d+)[^\d]*.*", r"\1", str(num))
                if int(num) < 10:
                    snum += '0'
                snum += str(num)
                version += snum
            if int(version) < 10000:
                version = int(version) * 100
            self._pg_version = int(version)

        if key == 'client_encoding':
            # Change encoding to client_encoding

            # Default encoding
            encoding = 'UTF-8'
            try:
                codecs.lookup(value)
                encoding = value
            except LookupError:
                pass

            self._encoding = encoding
            self._protocol.set_encoding(encoding)

    def connect(self,):
        """
        Connect to the database.
        """
        # Create and connect a new socket
        tmp_socket = self._create_new_socket()
        # Wrap with SSL
        self._wrap_ssl_socket(tmp_socket)
        # Set socket timeout
        self.set_timeout(self._default_timeout)
        # Startup
        data = self._protocol.startup(self._user,
                                      self._database,
                                      self._replication)
        self._socket_send(data)
        # Get messages from socket output
        self._socket_read()
        messages = list(self._get_messages(self._message_buffer.get_messages))
        # Test if the first message is an error
        self._check_message_error(messages[0])
        # If auth. method not implemented, raise an error
        if not self._protocol.is_auth_supported(messages[0]):
            raise error('PGC102', 'FATAL',
                        "Authentication method not supported")

        if self._protocol.is_auth_md5(messages[0]):
            if not self._password:
                raise error('PGC108', 'FATAL', "No password supplied")
            # MD5
            password = "md5" + hashlib.md5(
                hashlib.md5(
                    self._password.encode(self._encoding) +
                    self._user.encode(self._encoding)
                ).hexdigest().encode() +
                self._protocol.get_salt(messages[0])
            ).hexdigest()
            data = self._protocol.password_message(password)
            self._socket_send(data)
            self._socket_read()
            messages = list(self._get_messages(
                self._message_buffer.get_messages))
        elif self._protocol.is_auth_cleartext(messages[0]):
            # Cleartext
            data = self._protocol.password_message(self._password)
            self._socket_send(data)
            self._socket_read()
            messages = list(self._get_messages(
                self._message_buffer.get_messages))

        for message in messages:
            # Treat all messages.
            self._check_message_error(message)
            if self._protocol.is_auth_ok(message):
                self._is_auth = True
            elif self._protocol.is_parameter_status(message[0]):
                for key, val in message[1].items():
                    self._set_parameter_status(key, val)
            elif self._protocol.is_backend_key_data(message[0]):
                self._backend_key = message[1]['key']
                self._backend_pid = message[1]['pid']
            elif self._protocol.is_ready_for_query(message[0]):
                self._is_backend_ready = True
        # Ultimate check.
        if not self._is_auth:
            raise error('PGC103', 'FATAL', "Unable to connect.")
        if not self._is_backend_ready:
            raise error('PGC104', 'FATAL', "Backend not ready.")

    def close(self,):
        """
        Close the connection to the database.
        """
        data = self._protocol.terminate()
        self._socket_send(data)
        self._socket.close()

    def execute(self, query, parameters=None):
        """
        Execute a query and fetch the results.
        """
        if parameters:
            self._query = self._build_query(query, parameters)
        else:
            self._query = query
        self._rows = []
        self._nb_rows = None
        data = self._protocol.query(self._query)
        self._socket_send(data)
        self._socket_read()
        self.get_nb_rows()

    def _build_query(self, query, parameters):
        """
        Build a query using an input string and parameters (tuple).
        Matching pattern for replacement is '%s'.
        Supported types are: int, float, str, datetime.date, datetime.datetime.
        """
        pp = list()
        for p in parameters:
            if type(p) is str:
                p = "'%s'" % (re.sub(r"('|\\)", r"\\\1", p))
            elif type(p) in (datetime.date, datetime.datetime):
                p = "'%s'" % (p)
            elif type(p) in (int, float):
                p = str(p)
            else:
                raise Exception("Unsupported type %s." % (type(p)))
            pp.append(p)
        return query % tuple(pp)

    def begin(self,):
        """
        Start a new transaction.
        """
        self.execute("BEGIN")

    def commit(self,):
        """
        Commit current transaction.
        """
        self.execute("COMMIT")

    def rollback(self,):
        """
        Rollback current transaction.
        """
        self.execute("ROLLBACK")

    def get_rows(self,):
        """
        Get rows stored in self._rows.
        """
        row_desc = None
        for message in self._get_messages(self._message_buffer.get_messages):
            if self._protocol.is_row_description(message[0]):
                row_desc = message[1]
            elif self._protocol.is_data_row(message[0]):
                if row_desc is not None:
                    row = {}
                    i = 0
                    for value in message[1]:
                        if row_desc[i]['type_oid'] in [20, 21, 23]:
                            # Convert PG int2, int4 and int8 to python int()
                            try:
                                row[row_desc[i]['name']] = int(value)
                            except Exception:
                                row[row_desc[i]['name']] = None
                        elif row_desc[i]['type_oid'] in [700, 701, 1700]:
                            # Convert PG float4, float8 and numeric to python
                            # float()
                            try:
                                row[row_desc[i]['name']] = float(value)
                            except Exception:
                                row[row_desc[i]['name']] = None
                        elif row_desc[i]['type_oid'] == 16:
                            # Convert PG boolean to python's
                            if value == 't':
                                row[row_desc[i]['name']] = True
                            else:
                                row[row_desc[i]['name']] = False
                        else:
                            row[row_desc[i]['name']] = value
                        i += 1
                else:
                    # If don't have rows descriptions
                    # then store them as tuple.
                    row = tuple(message[1])
                yield row
            elif self._protocol.is_copy_data(message[0]):
                yield message[1]
            elif self._protocol.is_command_complete(message[0]):
                self._nb_rows = message[1]['nb_rows']
            elif self._protocol.is_empty_query_response(message[0]):
                self._nb_rows = 0
            else:
                self._check_message_error(message)

    def get_nb_rows(self,):
        """
        Get number of rows affected by the current query.
        """
        if self._nb_rows is None:
            for _ in self.get_rows():
                pass
        return self._nb_rows

    def set_timeout(self, timeout):
        """
        Set socket timeout value, if None: no timeout.
        """
        self._socket.settimeout(timeout)

    def get_timeout(self,):
        """
        Get socket timeout value.
        """
        return self._socket.gettimeout()

    def get_pg_version(self,):
        """
        Get PostgreSQL version.
        """
        return self._pg_version
