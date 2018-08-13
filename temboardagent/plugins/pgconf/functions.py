import logging
import os
import re
from collections import namedtuple

from temboardagent.spc import pg_escape, error
from temboardagent.errors import HTTPError, NotificationError
from temboardagent.tools import validate_parameters
from temboardagent.notification import NotificationMgmt, Notification
from .types import (
    T_FILE_VERSION,
    T_NEW_VERSION,
    T_PGSETTINGS_FILTER,
)
from .hba import (
    HBAComment,
    HBAEntry,
    HBAManager,
)


logger = logging.getLogger(__name__)


class FileSetting(namedtuple('FileSetting', ['name', 'setting', 'sourcefile',
                                             'sourceline'])):
    pass


def get_settings_categories(conn):
    query = """
SELECT DISTINCT(category) FROM pg_settings ORDER BY category
    """
    ret = {'categories': []}
    conn.execute(query)
    for row in conn.get_rows():
        ret['categories'].append(row['category'])
    return ret


def get_setting(conn, name):
    conn.execute("SELECT setting FROM pg_settings WHERE name = '%s'" % (name))
    return list(conn.get_rows())[0]['setting']


def get_files_configuration(conn):
    # Read settings from configuration files

    # First, we need to know location of all configuration files
    config_file = get_setting(conn, 'config_file')
    config_dir = os.path.dirname(config_file)

    # Get include files and directory from the main configuration file
    configuration = parse_configuration_file(config_file)
    includes = []
    for name in ['include_dir', 'include_if_exists', 'include']:
        fs = configuration.get(name, None)
        if fs:
            includes.append(fs)

    # Build configuration files list
    config_files = []
    for fs in sorted(includes, key=lambda x: x.sourceline):
        include_path = fs.setting.strip("'")
        if not os.path.isabs(include_path):
            include_path = os.path.join(config_dir, include_path)
        if os.path.isdir(include_path):
            # include_dir case
            files_inc = []
            for f in os.listdir(include_path):
                f_path = os.path.join(include_path, f)
                if f.endswith('.conf') and os.path.isfile(f_path):
                    files_inc.append(f)
            for sf in sorted(files_inc):
                config_files.append(os.path.join(include_path, sf))
        else:
            config_files.append(include_path)
    # At this point config_files contains the list of all files we need to
    # parse, ordered the right way to respect postgres precedense
    # It does not include postgresql.auto.conf
    for config_file in config_files:
        configuration = parse_configuration_file(config_file, configuration)

    return configuration


def preformat(setting, type):
    if setting.startswith("'") and setting.endswith("'"):
        setting = setting[1:-1]
    if type == u'bool':
        if setting == 'true':
            setting = 'on'
        elif setting == 'false':
            setting = 'off'
    return setting


def format_setting(setting, type, unit=None):
    if not setting:
        return
    if type == u'integer':
        setting = int(human_to_number(setting, unit))
    elif type == u'real':
        setting = float(setting)
    return setting


def get_settings(conn, http_context=None):
    # get configuration from files
    files_conf = get_files_configuration(conn)
    # get auto config
    data_directory = get_setting(conn, 'data_directory')
    autoconfig_file = os.path.join(data_directory, 'postgresql.auto.conf')
    auto_conf = parse_configuration_file(autoconfig_file, {})

    filter_query = ''
    if http_context and 'filter' in http_context['query']:
        # Check 'filter' parameters.
        validate_parameters(http_context['query'], [
            ('filter', T_PGSETTINGS_FILTER, True)
        ])
        filter = http_context['query']['filter'][0]
        filter_query = " WHERE name ILIKE '%{0}%'" \
                       " OR short_desc ILIKE '%{0}%'" \
                       " OR extra_desc ILIKE '%{0}%'".format(filter)
    query = """
SELECT
    name, setting, current_setting(name) AS current_setting, unit,
    vartype, min_val, max_val, enumvals, context, category,
    short_desc||' '||coalesce(extra_desc, '') AS desc, boot_val
FROM pg_settings
%s ORDER BY category, name
    """ % (filter_query)
    conn.execute(query)
    ret = []
    do_not_format_names = ['unix_socket_permissions']
    for row in conn.get_rows():
        if http_context and len(http_context['urlvars']) > 0:
            if http_context['urlvars'][0] != row['category']:
                continue
        cat_exists = False
        i = 0
        for ret_cat in ret:
            if ret_cat['category'] == row['category']:
                cat_exists = True
                break
            i += 1
        row_dict = {
            'name': row['name'],
            'setting': row['setting'],
            'setting_raw': row['current_setting'],
            'unit': row['unit'],
            'vartype': row['vartype'],
            'min_val': row['min_val'],
            'max_val': row['max_val'],
            'boot_val': row['boot_val'],
            'auto_val': None,
            'auto_val_raw': None,
            'file_val': None,
            'file_val_raw': None,
            'enumvals': row['enumvals'],
            'context': row['context'],
            'desc': row['desc']
        }

        name = row['name']

        if name in auto_conf:
            setting = preformat(auto_conf[name].setting, row['vartype'])
            row_dict['auto_val'] = setting
            row_dict['auto_val_raw'] = setting

        if name in files_conf:
            setting = preformat(files_conf[name].setting, row['vartype'])
            row_dict['file_val'] = setting
            row_dict['file_val_raw'] = setting

        if name not in do_not_format_names:
            for e in ['setting', 'min_val', 'max_val', 'boot_val', 'auto_val',
                      'file_val']:
                row_dict[e] = format_setting(row_dict[e], row['vartype'],
                                             row_dict['unit'])

        if not cat_exists:
            ret.append({'category': row['category'], 'rows': [row_dict]})
        else:
            ret[i]['rows'].append(row_dict)

    return ret


def human_to_number(h_value, h_unit=None):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'YB', 'ZB']
    re_unit = re.compile(r'([0-9.]+)\s*([KMGBTPEYZ]?B)$', re.IGNORECASE)
    m_value = re_unit.match(str(h_value))
    factor = 1
    if h_unit:
        m_unit = re_unit.match(str(h_unit))
        if m_unit:
            factor = int(m_unit.group(1))
            h_unit = str(m_unit.group(2))

    if m_value:
        p_num = m_value.group(1)
        p_unit = m_value.group(2)
        m = 0
        for u in units:
            if h_unit and h_unit.lower() == u.lower():
                m = 0
            if u.lower() == p_unit.lower():
                return (int(p_num) * (1024 ** m)) / factor
            else:
                m += 1

    # Valid time units are ms (milliseconds), s (seconds), min (minutes),
    # h (hours), and d (days
    re_unit = re.compile(r'([0-9.]+)\s*(ms|s|min|h|d)$')
    m_unit = re_unit.match(str(h_value))
    if h_unit == 'ms':
        mult = {'ms': 1, 's': 1000, 'min': 60000, 'h': 3600000, 'd': 86400000}
    elif h_unit == 's':
        mult = {'ms': -1000, 's': 1, 'min': 60, 'h': 3600, 'd': 86400}
    elif h_unit == 'min':
        mult = {'ms': -60000, 's': -60, 'min': 1, 'h': 60, 'd': 1440}
    elif h_unit == 'h':
        mult = {'ms': -3600000, 's': -3600, 'min': -60, 'h': 1, 'd': 24}
    elif h_unit == 'd':
        mult = {'ms': -86400000, 's': -86400, 'min': -1440, 'h': -24, 'd': 1}
    else:
        mult = {'ms': 1, 's': 1, 'min': 1, 'h': 1, 'd': 1}

    if m_unit:
        p_num = m_unit.group(1)
        p_unit = m_unit.group(2)
        if mult[p_unit] > 0:
            return (int(p_num) * mult[p_unit])
        else:
            return (int(p_num) / abs(mult[p_unit]))

    return h_value


def parse_configuration_file(file_path, ret={}):
    if not os.path.isfile(file_path):
        return ret
    try:
        with open(file_path, 'r') as fp:
            file_content = fp.read()
        fp.close()
        reg_conf_entry = re.compile(r'^\s*([\w\.]+)\s*=\s*([^#]+)\s*(#.*)?$')
        lno = 0
        for line in file_content.split('\n'):
            lno += 1
            m_conf = reg_conf_entry.match(line.strip())
            if m_conf:
                name = m_conf.group(1).strip()
                setting = m_conf.group(2).strip()
                ret[name] = FileSetting(name, setting, file_path, lno)
        return ret
    except IOError:
        raise HTTPError(500, "Internal error.")


def get_settings_status(conn):
    settings = get_settings(conn)
    pending_restart_changes = []
    pending_reload_changes = []
    pending_reload = False
    pending_restart = False
    differ = False
    for category in settings:
        for row in category['rows']:
            differ = False
            if row['auto_val'] is not None and \
               row['auto_val'] != row['setting']:
                differ = True
                row['pending_val'] = row['auto_val_raw']
            if row['auto_val'] is None and row['file_val'] and \
               row['file_val'] != row['setting']:
                differ = True
                row['pending_val'] = row['file_val_raw']
            if differ:
                if row['context'] in \
                   ['backend', 'user', 'superuser', 'sighup']:
                    pending_reload = True
                    pending_reload_changes.append(row)
                elif row['context'] in ['postmaster']:
                    pending_restart = True
                    pending_restart_changes.append(row)
    return {
        'restart_pending': pending_restart,
        'reload_pending': pending_reload,
        'restart_changes': pending_restart_changes,
        'reload_changes': pending_reload_changes
    }


def post_settings(conn, config, http_context):
    if http_context and 'filter' in http_context['query']:
        # Check 'filter' parameters.
        validate_parameters(http_context['query'], [
            ('filter', T_PGSETTINGS_FILTER, True)
        ])
    pg_config_categories = get_settings(conn, http_context)
    if 'settings' not in http_context['post']:
        raise HTTPError(406, "Parameter 'settings' not sent.")
    settings = http_context['post']['settings']
    ret = {'settings': []}
    do_not_check_names = ['unix_socket_permissions', 'log_file_mode']
    logger.debug(settings)
    for setting in settings:
        if 'name' not in setting \
           or 'setting' not in setting:
            raise HTTPError(406, "setting item malformed.")
        checked = False
        try:
            for pg_config_category in pg_config_categories:
                for item in pg_config_category['rows']:
                    if item['name'] == setting['name']:
                        if item['name'] in do_not_check_names:
                            checked = True
                            raise Exception()
                        if item['vartype'] == u'integer':
                            # Integers handling.
                            if item['min_val'] and \
                               item['unit'] and \
                               (int(human_to_number(setting['setting'],
                                    item['unit'])) <
                                   int(item['min_val'])):
                                raise HTTPError(406, "%s: Invalid setting." %
                                                     (item['name']))
                            if item['max_val'] and \
                               item['unit'] and \
                               (int(human_to_number(setting['setting'],
                                    item['unit'])) >
                                   int(item['max_val'])):
                                raise HTTPError(406, "%s: Invalid setting." %
                                                     (item['name']))
                            setting['setting'] = pg_escape(setting['setting'])
                            if ((setting['setting'].startswith("'") and
                                 setting['setting'].endswith("'")) or
                                (setting['setting'].startswith('"') and
                                 setting['setting'].endswith('"'))):
                                setting['setting'] = setting['setting'][1:-1]
                            if setting['setting'] == '':
                                setting['setting'] = None
                            checked = True
                        if item['vartype'] == u'real':
                            # Real handling.
                            if item['min_val'] and \
                               (float(setting['setting']) <
                                   float(item['min_val'])):
                                raise HTTPError(406, "%s: Invalid setting." %
                                                     (item['name']))
                            if item['max_val'] and \
                               (float(setting['setting']) >
                                   float(item['max_val'])):
                                raise HTTPError(406, "%s: Invalid setting." %
                                                     (item['name']))
                            setting['setting'] = float(setting['setting'])
                            checked = True
                        if item['vartype'] == u'bool':
                            # Boolean handling.
                            if setting['setting'].lower() not in \
                               [u'on', u'off']:
                                raise HTTPError(
                                    406, 'Invalid setting: %s.' %
                                         (setting['setting'].lower()))
                            checked = True
                        if item['vartype'] == u'enum':
                            # Enum handling.
                            if len(item['enumvals']) > 0:
                                enumvals = [
                                    re.sub(r"^[\"\'](.+)[\"\ ']$",
                                           r"\1", enumval)
                                    for enumval
                                    in item['enumvals'][1:-1].split(',')]
                                if ((setting['setting'].startswith("'") and
                                     setting['setting'].endswith("'")) or
                                    (setting['setting'].startswith('"') and
                                     setting['setting'].endswith('"'))):
                                    setting['setting'] = \
                                        setting['setting'][1:-1]
                                if setting['setting'] not in enumvals:
                                    raise HTTPError(
                                        406,
                                        'Invalid setting: %s.' %
                                        (setting['setting']))
                                checked = True
                        if item['vartype'] == u'string':
                            # String handling.
                            # setting must be escaped.
                            setting['setting'] = pg_escape(
                                str(setting['setting']))
                            if ((setting['setting'].startswith("'") and
                                 setting['setting'].endswith("'")) or
                                (setting['setting'].startswith('"') and
                                 setting['setting'].endswith('"'))):
                                setting['setting'] = setting['setting'][1:-1]
                            if setting['setting'] == '':
                                setting['setting'] = None
                            checked = True
                        raise Exception()
        except HTTPError as e:
            raise HTTPError(e.code, e.message['error'])
        except Exception as e:
            pass
        if not checked:
            raise HTTPError(406, 'Parameter %s can\'t be checked.' %
                                 (setting['name']))
        if 'force' not in setting:
            setting['force'] = 'false'
        if ((item['vartype'] == u'integer' and
            setting['setting'] != item['setting_raw']) or
            (item['vartype'] == u'real' and
            float(setting['setting']) != float(item['setting'])) or
            (item['vartype'] not in [u'integer', u'real'] and
            setting['setting'] != item['setting'])) or \
                (setting['force'] == 'true'):
            # At this point, all incoming parameters have been checked.
            if setting['setting']:
                query = "ALTER SYSTEM SET %s TO '%s'" % (setting['name'],
                                                         setting['setting'])
            else:
                query = "ALTER SYSTEM RESET %s;" % (setting['name'])

            logger.debug(query)

            # Push a notification on setting change.
            try:
                NotificationMgmt.push(
                    config,
                    Notification(
                        username=http_context['username'],
                        message="Setting '%s' changed: '%s' -> '%s'" % (
                            item['name'],
                            item['setting_raw'],
                            setting['setting'])))
            except NotificationError as e:
                logger.error(e.message)

            try:
                conn.execute(query)
            except error as e:
                raise HTTPError(408, "%s: %s" % (setting['name'], e.message))
            ret['settings'].append({
                'name': item['name'],
                'setting': setting['setting'],
                'previous_setting': item['setting_raw'],
                'restart': True if item['context'] in
                ['internal', 'postmaster'] else False
            })
    # Reload PG configuration.
    conn.execute("SELECT pg_reload_conf()")
    # Push a notification.
    try:
        NotificationMgmt.push(config,
                              Notification(username=http_context['username'],
                                           message="PostgreSQL reload"))
    except NotificationError as e:
        logger.error(e.message)

    return ret


"""
HBA
"""


def get_hba_raw(conn, http_context):
    version = None

    if http_context and 'version' in http_context['query']:
        # Check parameter 'version'
        validate_parameters(http_context['query'], [
            ('version', T_FILE_VERSION, True)
        ])
        version = http_context['query']['version'][0]

    ret = {
        'filepath': None,
        'version': version,
        'content': ''
    }
    hba_file = get_setting(conn, 'hba_file')
    ret['filepath'] = hba_file
    ret['content'] = HBAManager.get_file_content(hba_file, version)
    return ret


def get_hba(conn, http_context):
    version = None
    if http_context and 'version' in http_context['query']:
        # Check parameter 'version'
        validate_parameters(http_context['query'], [
            ('version', T_FILE_VERSION, True)
        ])
        version = http_context['query']['version'][0]

    ret = {
        'filepath': None,
        'version': version,
        'entries': []
    }
    hba_file = get_setting(conn, 'hba_file')
    ret['filepath'] = hba_file
    for hba_entry in HBAManager.get_entries(hba_file, version):
        ret['entries'].append(hba_entry.__dict__)
    return ret


def get_hba_versions(conn):
    hba_file = get_setting(conn, 'hba_file')
    return {
        'filepath': hba_file,
        'versions': HBAManager.get_versions(hba_file)
    }


def post_hba_raw(conn, config, http_context):
    new_version = False

    # Push a notification.
    try:
        NotificationMgmt.push(
            config,
            Notification(
                username=http_context['username'],
                message="HBA file updated"))
    except NotificationError as e:
        logger.error(e.message)

    if 'content' not in http_context['post']:
        raise HTTPError(406, "Parameter 'content' not sent.")
    if http_context and 'new_version' in http_context['post']:
        # Check parameter 'version'
        validate_parameters(http_context['post'], [
            ('new_version', T_NEW_VERSION, False)
        ])
        if http_context['post']['new_version'] is True:
            new_version = True

    hba_file = get_setting(conn, 'hba_file')
    return HBAManager.save_file_content(hba_file,
                                        http_context['post']['content'],
                                        new_version)


def post_hba(conn, config, http_context):
    new_version = False

    # Push a notification.
    try:
        NotificationMgmt.push(
            config,
            Notification(
                username=http_context['username'],
                message="HBA file updated"))
    except NotificationError as e:
        logger.error(e.message)

    if 'entries' not in http_context['post']:
        raise HTTPError(406, "Parameter 'entries' not sent.")

    if http_context and 'new_version' in http_context['post']:
        # Check parameter 'version'
        validate_parameters(http_context['post'], [
            ('new_version', T_NEW_VERSION, False)
        ])
        if http_context['post']['new_version'] is True:
            new_version = True

    hba_file = get_setting(conn, 'hba_file')
    hba_entries = []
    logger.debug(http_context['post']['entries'])
    for entry in http_context['post']['entries']:
        if 'comment' in entry and len(entry['connection']) == 0:
            new_hba_entry = HBAComment()
            new_hba_entry.comment = entry['comment']
        else:
            new_hba_entry = HBAEntry()
            try:
                new_hba_entry.connection = entry['connection'] \
                    if 'connection' in entry else ''
                new_hba_entry.database = entry['database'] \
                    if 'database' in entry else ''
                new_hba_entry.user = entry['user'] \
                    if 'user' in entry else ''
                new_hba_entry.address = entry['address'] \
                    if 'address' in entry else ''
                new_hba_entry.auth_method = entry['auth_method'] \
                    if 'auth_method' in entry else ''
                new_hba_entry.auth_options = entry['auth_options'] \
                    if 'auth_options' in entry else ''
            except Exception as e:
                logger.error(e.message)
                raise HTTPError(406, "Invalid HBA entry.")
            new_hba_entry.lazy_check()
        hba_entries.append(new_hba_entry)
    return HBAManager.save_entries(hba_file, hba_entries, new_version)


def delete_hba_version(conn, config, http_context):
    version = None

    if http_context and 'version' in http_context['query']:
        # Check parameter 'version'
        validate_parameters(http_context['query'], [
            ('version', T_FILE_VERSION, True)
        ])
        version = http_context['query']['version'][0]
    if version is None:
        raise HTTPError(406, "HBA version number must be specified.")

    hba_file = get_setting(conn, 'hba_file')
    # Push a notification.
    try:
        NotificationMgmt.push(
            config,
            Notification(
                username=http_context['username'],
                message="HBA file version '%s' removed." % (version)))
    except NotificationError as e:
        logger.error(e.message)

    return HBAManager.remove_version(hba_file, version)


def get_hba_options(conn):
    return HBAManager.options(conn)


"""
pg_ident
"""


def get_pg_ident(conn):
    ret = {
        'filepath': None,
        'content': ''
    }

    try:
        conn.execute("""
            SELECT setting
            FROM pg_settings
            WHERE name = 'ident_file'
        """)
        pg_ident_file = list(conn.get_rows())[0]['setting']
    except error as e:
        logger.error(str(e.message))
        raise HTTPError(500, 'Internal error.')

    ret['filepath'] = pg_ident_file
    with open(pg_ident_file, 'r') as fd:
        pg_ident_data = fd.read()
    fd.close()
    ret['content'] = pg_ident_data
    return ret


def post_pg_ident(conn, config, http_context):
    if 'content' not in http_context['post']:
        raise HTTPError(406, "Parameter 'content' not sent.")
    try:
        conn.execute("""
            SELECT setting
            FROM pg_settings
            WHERE name = 'ident_file'
        """)
        pg_ident_file = list(conn.get_rows())[0]['setting']
    except error as e:
        logger.error(str(e.message))
        raise HTTPError(500, 'Internal error.')

    with open(pg_ident_file, 'r') as fd:
        pg_ident_data = fd.read()
        fd.close()
        try:
            with open(pg_ident_file + ".previous", 'w') as fdp:
                fdp.write(pg_ident_data)
                fdp.close()
        except Exception as e:
            raise HTTPError(500, 'Internal error.')

    with open(pg_ident_file, 'w') as fd:
        fd.write(http_context['post']['content'])
        fd.close()
    return {'update': True}
