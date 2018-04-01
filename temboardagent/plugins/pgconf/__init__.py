from temboardagent.routing import add_route
from temboardagent.api_wrapper import (
    api_function_wrapper_pg,
)
import pgconf.functions as pgconf_functions
from pgconf.types import (
    T_PGSETTINGS_CATEGORY,
)


@add_route('GET', '/pgconf/configuration')
def get_pg_configuration(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings')


@add_route('GET', '/pgconf/configuration/categories')
def get_pg_configuration_categories(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings_categories')


@add_route('POST', '/pgconf/configuration')
def post_pg_configuration(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_settings')


@add_route('GET', '/pgconf/configuration/category/'+T_PGSETTINGS_CATEGORY)
def get_pg_configuration_category(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings')


@add_route('GET', '/pgconf/configuration/status')
def get_pg_configuration_status(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings_status')


@add_route('GET', '/pgconf/hba')
def get_pg_hba(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba')


@add_route('GET', '/pgconf/hba/raw')
def get_pg_hba_raw(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba_raw')


@add_route('POST', '/pgconf/hba')
def post_pg_hba(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_hba')


@add_route('POST', '/pgconf/hba/raw')
def post_pg_hba_raw(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_hba_raw')


@add_route('DELETE', '/pgconf/hba')
def delete_pg_hba(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'delete_hba_version')


@add_route('GET', '/pgconf/hba/versions')
def get_pg_hba_versions(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba_versions')


@add_route('GET', '/pgconf/pg_ident')
def get_pg_ident(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_pg_ident')


@add_route('POST', '/pgconf/pg_ident')
def post_pg_ident(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_pg_ident')


@add_route('GET', '/pgconf/hba/options')
def get_hba_options(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba_options')
