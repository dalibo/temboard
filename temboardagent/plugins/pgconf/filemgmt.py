import os.path
from os import listdir
import datetime
from temboardagent.errors import HTTPError


class ConfigurationFileManager:

    @classmethod
    def get_file_content(self, filepath, version=None):
        return read_file_content(filepath, version)

    @classmethod
    def save_file_content(self, filepath, filecontent, new_version=False):
        return save_file_content(filecontent, filepath, new_version)

    @classmethod
    def remove_version(self, filepath, version):
        return delete_file_version(filepath, version)

    @classmethod
    def get_versions(self, filepath):
        return get_file_versions(filepath)


def check_version_format(version):
    """
    Checks if a version number is well formed, eg:
        YYYY-MM-DDTHH:mm:ss
    """
    try:
        datetime.datetime.strptime(version, "%Y-%m-%dT%H:%M:%S")
        return True
    except Exception:
        raise HTTPError(406,
                        "Bad version format, should be 'YYYY-MM-DDTHH:mm:ss'")


def save_file_content(content, filepath, new_version=False):
    ret = {'last_version': None}
    if new_version is True and os.path.isfile(filepath):
        """
        When new_version param. is true, we need to save current file as a new
        version before writing new file content.
        """
        # Build new version's file path.
        dt_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        filepath_version = "%s.%s" % (filepath, dt_str)
        ret['last_version'] = dt_str
        # Read current version's content.
        cur_content = None
        with open(filepath, 'r') as fd:
            cur_content = fd.read()
        # Check if new version's file exists.
        if os.path.isfile(filepath_version):
            raise HTTPError(500, "Unable to create a new version, file %s "
                            "already exists." % (filepath_version))
        # Write current version's content in new version's file.
        with open(filepath_version, 'w') as fd:
            fd.write(cur_content)
    else:
        versions = get_file_versions(filepath)
        if len(versions) > 0:
            ret['last_version'] = versions[-1]

    # Write new file content into current file.
    with open(filepath, 'w') as fd:
        fd.write(content)

    ret['filepath'] = filepath
    return ret


def read_file_content(filepath, version=None):
    """
    Returns file content or content from a previsous version.
    """
    if version is not None:
        # Check the version is well formatted.
        check_version_format(version)
        filepath_version = "%s.%s" % (filepath, version)
        if not os.path.isfile(filepath_version):
            raise HTTPError(404, "Version %s of file %s does not exist."
                                 % (version, filepath))
        filepath = filepath_version

    with open(filepath, 'r') as fd:
        return fd.read()


def get_file_versions(filepath):
    """
    Returns a list of version number for a file path.
    """
    filedir = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    if not os.path.isdir(filedir):
        raise HTTPError(500, "Unable to list content from directory: %s"
                             % (filedir))
    if not os.path.isfile(filepath):
        raise HTTPError(404, "File %s does not exist." % (filepath))

    versions = []
    l_filename = len(filename)
    for f in listdir(filedir):
        try:
            if f[:l_filename] == filename \
               and check_version_format(f[l_filename + 1:]):
                """
                Let's consider f as one of the  previous version of the file
                if the first part of f's name is equal to original file name
                and the rest of f's name (-1 for the seperating dot) is a
                valid version number.
                """
                versions.append(f[l_filename + 1:])
        except Exception:
            pass
    # Return a sorted versions list.
    return sorted(versions, reverse=True)


def delete_file_version(filepath, version):
    """
    Remove a previous version of file.
    """
    check_version_format(version)
    if version in get_file_versions(filepath):
        filepath_version = "%s.%s" % (filepath, version)
        os.remove(filepath_version)
        return {'version': version, 'deleted': True}
    else:
        raise HTTPError(404, "Version %s of file %s does not exist."
                             % (version, filepath))
