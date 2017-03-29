from temboardagent.routing import add_route
from temboardagent.api_wrapper import (
    api_function_wrapper_pg,
)
from temboardagent.logger import set_logger_name
import pgconf.functions as pgconf_functions
from pgconf.types import (
    T_PGSETTINGS_CATEGORY,
)


@add_route('GET', '/pgconf/configuration')
@add_route('GET', '/settings/configuration')
def get_pg_configuration(http_context, queue_in=None, config=None,
                         sessions=None, commands=None):
    """
    @api {get} /pgconf/configuration Fetch all PostgreSQL settings.
    @apiVersion 0.0.1
    @apiName GetPgconfConfiguration
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object[]} response List of settings category.
    @apiSuccess {String}   response.category Category name.
    @apiSuccess {Object[]} response.rows List of settings.
    @apiSuccess {String}   response.rows.context Context required to set the parameter's value.
    @apiSuccess {String[]} response.rows.enum_vals Allowed values of an enum parameter (null for non-enum values).
    @apiSuccess {Number}   response.rows.min_val Minimum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {Number}   response.rows.max_val Maximum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {String}   response.rows.vartype Parameter type (bool, enum, integer, real, or string).
    @apiSuccess {String}   response.rows.auto_val Parameter value set in auto configuration file.
    @apiSuccess {String}   response.rows.auto_val_raw Parameter value set in auto configuration file (raw).
    @apiSuccess {String}   response.rows.file_val Parameter value set in main postgresql.conf file.
    @apiSuccess {String}   response.rows.file_val_raw Parameter value set in main postgresql.conf file (raw).
    @apiSuccess {String}   response.rows.boot_val Parameter value assumed at server startup if the parameter is not otherwise set.
    @apiSuccess {String}   response.rows.unit Implicit unit of the parameter.
    @apiSuccess {String}   response.rows.desc Parameter description.
    @apiSuccess {String}   response.rows.name Parameter name.
    @apiSuccess {String}   response.rows.setting Parameter value.
    @apiSuccess {String}   response.rows.setting_raw Parameter value (raw).

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/configuration

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        [
            {
                "category": "Autovacuum",
                "rows":
                [
                    {
                        "context": "sighup",
                        "enumvals": null,
                        "max_val": null,
                        "vartype": "bool",
                        "auto_val": "off",
                        "auto_val_raw": "off",
                        "boot_val": "on",
                        "unit": null,
                        "desc": "Starts the autovacuum subprocess.",
                        "name": "autovacuum",
                        "min_val": null,
                        "setting": "off",
                        "setting_raw": "off",
                        "file_val": null,
                        "file_val_raw": null
                    },
                    ...
                ]
            },
            ...
        ]

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings')


@add_route('GET', '/pgconf/configuration/categories')
@add_route('GET', '/settings/configuration/categories')
def get_pg_configuration_categories(http_context, queue_in=None, config=None,
                                    sessions=None, commands=None):
    """
    @api {get} /pgconf/configuration/categories Fetch settings categories names.
    @apiVersion 0.0.1
    @apiName GetPgconfConfigurationCategories
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {String[]} categories List of settings category name.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/configuration/categories

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "categories":
            [
                "Autovacuum",
                "Client Connection Defaults / Locale and Formatting",
                "Client Connection Defaults / Other Defaults",
                ...
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings_categories')


@add_route('POST', '/pgconf/configuration')
@add_route('POST', '/settings/configuration')
def post_pg_configuration(http_context, queue_in=None, config=None,
                          sessions=None, commands=None):
    """
    @api {post} /pgconf/configuration Update setting/s value.
    @apiVersion 0.0.1
    @apiName PostPgconfConfiguration
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam {Object[]} settings List of settings.
    @apiParam {String}   settings.name Setting name.
    @apiParam {String}   settings.setting Setting value.

    @apiSuccess {Object[]} settings List of settings updated.
    @apiSuccess {String}   settings.setting Setting value.
    @apiSuccess {Boolean}  settings.restart Does PostgreSQL need to be restarted.
    @apiSuccess {String}   settings.name Setting name.
    @apiSuccess {String}   settings.previous_setting Previous setting value.

    @apiExample {curl} Example usage:
        curl -k -X POST -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    -H "Content-Type: application/json" \
                    --data '{"settings": [{"name": "autovacuum", "setting": "on"}]}' \
                    https://localhost:2345/pgconf/configuration

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:57:52 GMT
        Content-type: application/json
        {
            "settings":
            [
                {
                    "setting": "on",
                    "restart": false,
                    "name": "autovacuum",
                    "previous_setting": "off"
                }
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.
    @apiError (406 error) error Setting item malformed.
    @apiError (400 error) error Invalid json format.


    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}


    @apiErrorExample 400 error example
        HTTP/1.0 400 Bad request
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid json format: Expecting ',' delimiter: line 1 column 51 (char 50)."}


    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_settings')


@add_route('GET', '/pgconf/configuration/category/'+T_PGSETTINGS_CATEGORY)
@add_route('GET', '/settings/configuration/category/'+T_PGSETTINGS_CATEGORY)
def get_pg_configuration_category(http_context, queue_in=None, config=None,
                                  sessions=None, commands=None):
    """
    @api {get} /pgconf/configuration/category/:categoryname Fetch settings for one category, based on categoryname.
    @apiVersion 0.0.1
    @apiName GetPgconfConfigurationCategory
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {String} categoryname Category Name.

    @apiSuccess {Object[]} response List of settings category.
    @apiSuccess {String}   response.category Category name.
    @apiSuccess {Object[]} response.rows List of settings.
    @apiSuccess {String}   response.rows.context Context required to set the parameter's value.
    @apiSuccess {String[]} response.rows.enum_vals Allowed values of an enum parameter (null for non-enum values).
    @apiSuccess {Number}   response.rows.min_val Minimum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {Number}   response.rows.max_val Maximum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {String}   response.rows.vartype Parameter type (bool, enum, integer, real, or string).
    @apiSuccess {String}   response.rows.auto_val Parameter value set in auto configuration file.
    @apiSuccess {String}   response.rows.auto_val_raw Parameter value set in auto configuration file (raw).
    @apiSuccess {String}   response.rows.file_val Parameter value set in main postgresql.conf file.
    @apiSuccess {String}   response.rows.file_val_raw Parameter value set in main postgresql.conf file (raw).
    @apiSuccess {String}   response.rows.boot_val Parameter value assumed at server startup if the parameter is not otherwise set.
    @apiSuccess {String}   response.rows.unit Implicit unit of the parameter.
    @apiSuccess {String}   response.rows.desc Parameter description.
    @apiSuccess {String}   response.rows.name Parameter name.
    @apiSuccess {String}   response.rows.setting Parameter value.
    @apiSuccess {String}   response.rows.setting_raw Parameter value (raw).


    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/configuration/category/Autovacuum"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Wed, 10 Feb 2016 09:56:30 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        [
            {
                "category": "Autovacuum",
                "rows":
                [
                    {
                        "context": "sighup",
                        "enumvals": null,
                        "max_val": null,
                        "vartype": "bool",
                        "auto_val": "on",
                        "auto_val_raw": "on",
                        "boot_val": "on",
                        "unit": null,
                        "desc": "Starts the autovacuum subprocess. ",
                        "name": "autovacuum",
                        "min_val": null,
                        "setting": "on",
                        "setting_raw": "on",
                        "file_val": null,
                        "file_val_raw": null
                    },
                    ...
                ]
            }
        ]

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings')


@add_route('GET', '/pgconf/configuration/status')
@add_route('GET', '/settings/configuration/status')
def get_pg_configuration_status(http_context, queue_in=None, config=None,
                                sessions=None, commands=None):
    """
    @api {get} /pgconf/configuration/status Shows settings waiting for PostgreSQL reload and/or restart
    @apiVersion 0.0.1
    @apiName GetPgconfConfigurationStatus
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object}    response
    @apiSuccess {Boolean}   response.restart_pending Does PostgreSQL need to be restarted ?
    @apiSuccess {Object[]}  response.restart_changes List of settings.
    @apiSuccess {String}    response.restart_changes.context Context required to set the parameter's value.
    @apiSuccess {String[]}  response.restart_changes.enum_vals Allowed values of an enum parameter (null for non-enum values).
    @apiSuccess {Number}    response.restart_changes.min_val Minimum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {Number}    response.restart_changes.max_val Maximum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {String}    response.restart_changes.vartype Parameter type (bool, enum, integer, real, or string).
    @apiSuccess {String}    response.restart_changes.auto_val Parameter value set in auto configuration file.
    @apiSuccess {String}    response.restart_changes.auto_val_raw Parameter value set in auto configuration file (raw).
    @apiSuccess {String}    response.restart_changes.file_val Parameter value set in main postgresql.conf file.
    @apiSuccess {String}    response.restart_changes.file_val_raw Parameter value set in main postgresql.conf file (raw).
    @apiSuccess {String}    response.restart_changes.boot_val Parameter value assumed at server startup if the parameter is not otherwise set.
    @apiSuccess {String}    response.restart_changes.unit Implicit unit of the parameter.
    @apiSuccess {String}    response.restart_changes.desc Parameter description.
    @apiSuccess {String}    response.restart_changes.name Parameter name.
    @apiSuccess {String}    response.restart_changes.setting Parameter value.
    @apiSuccess {String}    response.restart_changes.setting_raw Parameter value (raw).
    @apiSuccess {String}    response.restart_changes.pending_val Pending value.
    @apiSuccess {Boolean}   response.reload_pending Does PostgreSQL need to be reloaded ?
    @apiSuccess {Object[]}  response.reload_changes List of settings.
    @apiSuccess {String}    response.reload_changes.context Context required to set the parameter's value.
    @apiSuccess {String[]}  response.reload_changes.enum_vals Allowed values of an enum parameter (null for non-enum values).
    @apiSuccess {Number}    response.reload_changes.min_val Minimum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {Number}    response.reload_changes.max_val Maximum allowed value of the parameter (null for non-numeric values).
    @apiSuccess {String}    response.reload_changes.vartype Parameter type (bool, enum, integer, real, or string).
    @apiSuccess {String}    response.reload_changes.auto_val Parameter value set in auto configuration file.
    @apiSuccess {String}    response.reload_changes.auto_val_raw Parameter value set in auto configuration file (raw).
    @apiSuccess {String}    response.reload_changes.file_val Parameter value set in main postgresql.conf file.
    @apiSuccess {String}    response.reload_changes.file_val_raw Parameter value set in main postgresql.conf file (raw).
    @apiSuccess {String}    response.reload_changes.boot_val Parameter value assumed at server startup if the parameter is not otherwise set.
    @apiSuccess {String}    response.reload_changes.unit Implicit unit of the parameter.
    @apiSuccess {String}    response.reload_changes.desc Parameter description.
    @apiSuccess {String}    response.reload_changes.name Parameter name.
    @apiSuccess {String}    response.reload_changes.setting Parameter value.
    @apiSuccess {String}    response.reload_changes.setting_raw Parameter value (raw).
    @apiSuccess {String}    response.reload_changes.pending_val Pending value.



    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/configuration/status"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Wed, 10 Feb 2016 09:56:30 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "restart_changes":
            [
                {
                    "context": "postmaster",
                    "setting_raw": "128MB",
                    "enumvals": null,
                    "max_val": 1073741823,
                    "vartype": "integer",
                    "auto_val": 32768,
                    "file_val_raw": "128MB",
                    "boot_val": 1024,
                    "unit": "8kB",
                    "desc": "Sets the number of shared memory buffers used by the server. ",
                    "name": "shared_buffers",
                    "auto_val_raw": "256MB",
                    "min_val": 16,
                    "setting": 16384,
                    "file_val": 16384,
                    "pending_val": "256MB"
                }
            ],
            "restart_pending": true,
            "reload_pending": false,
            "reload_changes":
            [
            ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_settings_status')


@add_route('GET', '/pgconf/hba')
@add_route('GET', '/settings/hba')
def get_pg_hba(http_context, queue_in=None, config=None, sessions=None,
               commands=None):
    """
    @api {get} /pgconf/hba?version=:version Get pg_hba.conf records
    @apiVersion 0.0.1
    @apiName GetPgconfHBA
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {String} version Version number, if omitted, current file is considered.

    @apiSuccess {Object[]}  response.entries HBA records list.
    @apiSuccess {String}    response.entries.connection The record matches connection attempts using Unix-domain sockets (local) or using TCP/IP (host) or using TCP/IP, but only when the connection is made with SSL encryption (hostssl) or using TCP/IP that do not use SSL.
    @apiSuccess {String}    response.entries.database Specifies which database name(s) this record matches.
    @apiSuccess {String}    response.entries.user Specifies which user name(s) this record matches.
    @apiSuccess {String}    response.entries.address Specifies the client machine address(es) that this record matches. Hostname or IP address range.
    @apiSuccess {String}    response.entries.auth_method Specifies the authentication method to use when a connection matches this record.
    @apiSuccess {String}    response.entries.auth_options Specifies options for the authentication method.
    @apiSuccess {String}    response.version pg_hba.conf file version, null if current.
    @apiSuccess {String}    response.filepath pg_hba.conf file path.


    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/hba"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Wed, 10 Feb 2016 09:56:30 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json*
        {
            "entries":
            [
                {
                    "database": "all",
                    "connection": "local",
                    "auth_options": "",
                    "user": "postgres",
                    "address": "",
                    "auth_method": "ident"
                },
                ...
            ],
            "version": null,
            "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.
    @apiError (404 error) error File version not found.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    @apiErrorExample 404 error example
        HTTP/1.0 404 Not Found
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Thu, 11 Feb 2016 09:04:02 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json

        {"error": "Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba')


@add_route('GET', '/pgconf/hba/raw')
@add_route('GET', '/settings/hba/raw')
def get_pg_hba_raw(http_context, queue_in=None, config=None, sessions=None,
                   commands=None):
    """
    @api {get} /pgconf/hba/raw?version=:version Get pg_hba.conf raw content
    @apiVersion 0.0.1
    @apiName GetPgconfHBARaw
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {String} version Version number, if omitted, current file is considered.

    @apiSuccess {Object}  response
    @apiSuccess {Object}  response.content pg_hba.conf file raw content.
    @apiSuccess {String}  response.version pg_hba.conf file version, null if current.
    @apiSuccess {String}  response.filepath pg_hba.conf file path.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/hba/raw?version=2016-01-29T08:46:09"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Thu, 11 Feb 2016 13:40:51 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "content": "# PostgreSQL Client Authentication Configuration File\r\n# ===================================================\r\n# Database administrative login by Unix domain socket\r\nlocal   all             postgres                           ident #tutu\r\nlocal   all             all                                md5 #toto\r\n# TYPE  DATABASE        USER            ADDRESS                 METHOD\r\n# \"local\" is for Unix domain socket connections only\r\nlocal   all             all                                     md5\r\n# IPv4 local connections:\r\nhost    all             all             127.0.0.1/32            md5\r\n# IPv6 local connections:\r\nhost    all             all             ::1/128                 md5\r\n# Allow replication connections from localhost, by a user with the\r\n# replication privilege.\r\nlocal   replication     postgres                                peer\r\nhost    replication     postgres        127.0.0.1/32            md5\r\nhost    replication     postgres        ::1/128                 md5\r\nhost\treplication\t\treplicator\t\t192.168.1.40/32\t\t\ttrust #test\r\n# test ok\r\nhost    all     all     192.168.1.0/24  trust\r\nhost    all     all     192.168.1.0/24  trust\r\n",
            "version": "2016-01-29T08:46:07",
            "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.
    @apiError (404 error) error File version not found.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    @apiErrorExample 404 error example
        HTTP/1.0 404 Not Found
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Thu, 11 Feb 2016 09:04:02 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json

        {"error": "Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba_raw')


@add_route('POST', '/pgconf/hba')
@add_route('POST', '/settings/hba')
def post_pg_hba(http_context, queue_in=None, config=None, sessions=None,
                commands=None):
    """
    @api {post} /pgconf/hba Replace pg_hba.conf file content.
    @apiVersion 0.0.1
    @apiName PostPgconfHBA
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {Object[]} entries List of records.
    @apiParam  {String}   entries.connection The record matches connection attempts using Unix-domain sockets (local) or using TCP/IP (host) or using TCP/IP, but only when the connection is made with SSL encryption (hostssl) or using TCP/IP that do not use SSL.
    @apiParam  {String}   entries.database Specifies which database name(s) this record matches.
    @apiParam  {String}   entries.user Specifies which user name(s) this record matches.
    @apiParam  {String}   entries.address Specifies the client machine address(es) that this record matches. Hostname or IP address range.
    @apiParam  {String}   entries.auth_method Specifies the authentication method to use when a connection matches this record.
    @apiParam  {String}   entries.auth_options Specifies options for the authentication method.
    @apiParam  {Boolean}  new_version Create a new version of current pg_hba.conf before writing new content.

    @apiSuccess {Object}  response
    @apiSuccess {String}  response.last_version pg_hba.conf last file version.
    @apiSuccess {String}  response.filepath pg_hba.conf file path.

    @apiExample {curl} Example usage:
        curl -k -X POST -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                        -H "Content-Type: application/json" \
                        --data '{"entries": [{"connection": "local", "user": "all", "database": "all", "auth_method": "peer"}, ... ], "new_version": true}' \
                    https://localhost:2345/pgconf/hba"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Thu, 11 Feb 2016 14:26:19 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "last_version": "2016-02-11T15:26:19",
            "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}


    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_hba')


@add_route('POST', '/pgconf/hba/raw')
@add_route('POST', '/settings/hba/raw')
def post_pg_hba_raw(http_context, queue_in=None, config=None, sessions=None,
                    commands=None):
    """
    @api {post} /pgconf/hba/raw Replace pg_hba.conf file content (raw mode).
    @apiVersion 0.0.1
    @apiName PostPgconfHBARaw
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {String}   content pg_hba.conf content (raw).
    @apiParam  {Boolean}  new_version Create a new version of current pg_hba.conf before writing new content.

    @apiSuccess {Object}  response
    @apiSuccess {String}  response.last_version pg_hba.conf last file version.
    @apiSuccess {String}  response.filepath pg_hba.conf file path.

    @apiExample {curl} Example usage:
        curl -k -X POST -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                        -H "Content-Type: application/json" \
                        --data '{"content": "local all all md5\r\n ...", "new_version": true}' \
                    https://localhost:2345/pgconf/hba/raw"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Thu, 11 Feb 2016 14:26:19 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "last_version": "2016-02-11T15:26:19",
            "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}


    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_hba_raw')


@add_route('DELETE', '/pgconf/hba')
@add_route('DELETE', '/settings/hba')
def delete_pg_hba(http_context, queue_in=None, config=None, sessions=None,
                  commands=None):
    """
    @api {delete} /pgconf/hba?version=:version Remove a previous pg_hba.conf version.
    @apiVersion 0.0.1
    @apiName DeletePgconfHBA
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {String} version Version number.

    @apiSuccess {Object}  response
    @apiSuccess {String}  response.version pg_hba.conf version.
    @apiSuccess {Boolean} response.deleted Is deleted ?

    @apiExample {curl} Example usage:
        curl -k -X DELETE -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/hba?version=2016-01-29T08:44:26"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Fri, 12 Feb 2016 09:54:17 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "deleted": true,
            "version": "2016-01-29T08:44:26"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.
    @apiError (404 error) error File version not found.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    @apiErrorExample 404 error example
        HTTP/1.0 404 Not Found
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Fri, 12 Feb 2016 10:00:55 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json

        {"error": "Version 2016-01-29T08:44:26 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist."}
    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'delete_hba_version')


@add_route('GET', '/pgconf/hba/versions')
@add_route('GET', '/settings/hba/versions')
def get_pg_hba_versions(http_context, queue_in=None, config=None,
                        sessions=None, commands=None):
    """
    @api {get} /pgconf/hba/versions Get the list of pg_hba.conf versions.
    @apiVersion 0.0.1
    @apiName GetPgconfHBAVersions
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object}   response
    @apiSuccess {String[]} response.versions List of versions, desc. sorting.
    @apiSuccess {String}   response.filepath pg_hba.conf file path.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/hba/versions"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Fri, 12 Feb 2016 10:38:10 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "versions":
            [
                "2016-02-11T18:01:35",
                "2016-02-11T16:43:51",
                "2016-02-11T16:43:36",
                ...
            ],
            "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"}

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba_versions')


@add_route('GET', '/pgconf/pg_ident')
@add_route('GET', '/settings/pg_ident')
def get_pg_ident(http_context, queue_in=None, config=None, sessions=None,
                 commands=None):
    """
    @api {get} /pgconf/pg_ident Get pg_ident.conf raw content
    @apiVersion 0.0.1
    @apiName GetPgconfPGIdentRaw
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object}  response
    @apiSuccess {Object}  response.content pg_ident.conf file raw content.
    @apiSuccess {String}  response.filepath pg_ident.conf file path.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/pg_ident"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Fri, 12 Feb 2016 10:48:57 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "content": "# PostgreSQL User Name Maps\r\n# =========================\r\n ... ",
            "filepath": "/etc/postgresql/9.4/main/pg_ident.conf"
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_pg_ident')


@add_route('POST', '/pgconf/pg_ident')
@add_route('POST', '/settings/pg_ident')
def post_pg_ident(http_context, queue_in=None, config=None, sessions=None,
                  commands=None):
    """
    @api {post} /pgconf/pg_ident Replace pg_ident.conf file content (raw mode).
    @apiVersion 0.0.1
    @apiName PostPgconfPGIdentRaw
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiParam  {String}   content pg_ident.conf content (raw).

    @apiSuccess {Object}  response
    @apiSuccess {Boolean} response.update Has pg_ident.conf been updated ?

    @apiExample {curl} Example usage:
        curl -k -X POST -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                        -H "Content-Type: application/json" \
                        --data '{"content": "# PostgreSQL User Name Maps\r\n ..."}' \
                    https://localhost:2345/pgconf/pg_ident"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Thu, 11 Feb 2016 14:26:19 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "update": true
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}
    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'post_pg_ident')


@add_route('GET', '/pgconf/hba/options')
@add_route('GET', '/settings/hba/options')
def get_hba_options(http_context, queue_in=None, config=None, sessions=None,
                    commands=None):
    """
    @api {get} /pgconf/hba/options Get HBA potential values for each column.
    @apiVersion 0.0.1
    @apiName GetPgconfHBAOptions
    @apiGroup Pgconf

    @apiHeader {String} X-Session Session ID.

    @apiSuccess {Object}    response
    @apiSuccess {String[]}  response.connection Connection field potential values.
    @apiSuccess {String[]}  response.database Database field potential values.
    @apiSuccess {String[]}  response.user User field potential values.
    @apiSuccess {String[]}  response.auth_method Authentication methods.

    @apiExample {curl} Example usage:
        curl -k -H "X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e" \
                    https://localhost:2345/pgconf/hba/options"

    @apiSuccessExample Success-Reponse:
        HTTP/1.0 200 OK
        Server: temboard-agent/0.0.1 Python/2.7.9
        Date: Fri, 12 Feb 2016 10:48:57 GMT
        Access-Control-Allow-Origin: *
        Content-type: application/json
        {
            "connection": [ "local", "host", "hostssl", "hostnossl" ],
            "database": [ "all", "sameuser", "samerole", "db1" ],
            "user": [ "all", "user1", "+group1" ],
            "auth_method": [ "trust", "reject", ... ]
        }

    @apiError (500 error) error Internal error.
    @apiError (401 error) error Invalid session.
    @apiError (406 error) error Parameter 'X-Session' is malformed.

    @apiErrorExample 401 error example
        HTTP/1.0 401 Unauthorized
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Invalid session."}

    @apiErrorExample 406 error example
        HTTP/1.0 406 Not Acceptable
        Server: temboard-agent/0.0.1 Python/2.7.8
        Date: Wed, 22 Apr 2015 09:58:00 GMT
        Content-type: application/json

        {"error": "Parameter 'X-Session' is malformed."}

    """  # noqa
    set_logger_name("pgconf")
    return api_function_wrapper_pg(config, http_context, sessions,
                                   pgconf_functions, 'get_hba_options')
