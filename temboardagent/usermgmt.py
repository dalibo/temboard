import base64
import time
from hashlib import sha256, sha512
from os import urandom
from binascii import hexlify

from temboardagent.errors import ConfigurationError, HTTPError


def hash_password(username, password):
    """
    Hash a password with the following formula:
        sha512(password + sha512(username))
    """
    bytes_password = hexlify(password.encode('utf-8'))
    bytes_sha_username = sha512(username.encode('utf-8')).digest()
    hpasswd = sha512(bytes_password + bytes_sha_username).digest()
    return base64.b64encode(hpasswd)


def read_password_file(filepath):
    """
    Read and return the user/password file.
    """
    try:
        with open(filepath, 'r') as fd:
            lines = fd.readlines()
            fd.close()
            return lines
    except IOError:
        raise ConfigurationError("Can't open password file for reading.")


def get_user(filepath, username):
    """
    Get a user/passwd form the file.
    """
    for line in read_password_file(filepath):
        line = line.strip()
        if not line:
            continue
        l_username, l_hpasswd = line.split(':')
        if username == l_username:
            return (l_username, l_hpasswd)
    raise HTTPError(404, 'Invalid username/password.')


def auth_user(filepath, username, password):
    """
    Hash and compair the given couple username/password.
    """
    (l_username, l_hpasswd) = get_user(filepath, username)
    n_hpasswd = hash_password(username, password)
    if n_hpasswd.decode('utf-8') != l_hpasswd:
        raise HTTPError(404, 'Invalid username/password.')


def gen_sessionid(username):
    """
    Sessionid generator.
    """
    bytes_sha_username = sha512(username.encode('utf-8')).digest()
    bytes_rand = hexlify(urandom(32))
    bytes_time = hexlify(str(time.time() * 1000).encode('utf-8'))
    return sha256(bytes_sha_username + bytes_rand + bytes_time).hexdigest()
