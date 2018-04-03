.. _pgconf_api:

PgConf plugin API
=================

.. http:get:: /pgconf/configuration

    Get PostgreSQL settings from ``pg_settings`` system view and configuration files.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /pgconf/configuration HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
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
                }
            ]
        }
    ]


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 401 Unauthorized
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:58:00 GMT
    Content-type: application/json

    {"error": "Invalid session."}


.. sourcecode:: http

    HTTP/1.0 406 Not Acceptable
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:58:00 GMT
    Content-type: application/json

    {"error": "Parameter 'X-Session' is malformed."}


.. http:get:: /pgconf/configuration/categories

    Get list of settings categories.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /pgconf/configuration/categories HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "categories":
        [
            "Autovacuum",
            "Client Connection Defaults / Locale and Formatting",
            "Client Connection Defaults / Other Defaults"
        ]
    }


.. http:post:: /pgconf/configuration

    Update one or many PostgreSQL settings values. This API issues ``ALTER SYSTEM`` SQL statements.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` or setting item is malformed.
    :status 400: invalid JSON format.


**Example request**:

.. sourcecode:: http

    POST /pgconf/configuration HTTP/1.1
    Content-Type: application/json
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

    {
        "settings":
        [
            {
                "name": "autovacuum",
                "setting": "on"
            }
        ]
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
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


.. http:get:: /pgconf/configuration/category/(category_name)

    Get list of settings for one category, based on category name.

    :reqheader X-Session: Session ID
    :param category_name: Setting category name
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /pgconf/configuration/category/Autovacuum HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
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
                }
            ]
        }
    ]


.. http:get:: /pgconf/configuration/status

    Shows settings waiting for PostgreSQL server reload and/or restart

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /pgconf/configuration/status HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
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
        "reload_changes": []
    }


.. http:get:: /pgconf/hba

    Get records from the ``pg_hba.conf`` file.

    :query version: ``pg_hba.conf`` file version to get. Ex: ``2017-03-06T16:34:07``. If not set then the current version is read.
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 404: ``version`` does not exist
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example requests**:

.. sourcecode:: http

    GET /pgconf/hba HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


.. sourcecode:: http

    GET /pgconf/hba?version=2017-03-06T16:34:07 HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "entries":
        [
            {
                "comment": " \"local\" is for Unix domain socket connections only"
            },
            {
                "database": "all",
                "auth_options": "",
                "connection": "local",
                "user": "alice",
                "address": "",
                "auth_method": "trust"
            },
            {
                "database": "all",
                "auth_options": "",
                "connection": "local",
                "user": "all",
                "address": "",
                "auth_method": "trust"
            }
        ],
        "version": null,
        "filepath": "/etc/postgresql-9.5/pg_hba.conf"
    }


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 404 Not Found
    Server: temboard-agent/0.0.1 Python/2.7.9
    Date: Thu, 11 Feb 2016 09:04:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"error": "Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist."}


.. http:get:: /pgconf/hba/raw

    Get raw content of ``pg_hba.conf`` file.

    :query version: ``pg_hba.conf`` file version to get. Ex: ``2017-03-06T16:34:07``. If not set then the current version is read.
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 404: ``version`` does not exist
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example requests**:

.. sourcecode:: http

    GET /pgconf/hba/raw HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


.. sourcecode:: http

    GET /pgconf/hba/raw?version=2017-03-06T16:34:07 HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "content": "# \"local\" is for Unix domain socket connections only\r\nlocal  all  julien  trust \r\nlocal  all  all  trust \r\n# IPv4 local connections:\r\nhost  all  all 127.0.0.1/32 trust \r\n# IPv6 local connections:\r\nhost  all  all ::1/128 trust \r\n",
        "version": null,
        "filepath": "/etc/postgresql-9.5/pg_hba.conf"
    }


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 404 Not Found
    Server: temboard-agent/0.0.1 Python/2.7.9
    Date: Thu, 11 Feb 2016 09:04:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"error": "Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist."}


.. http:post:: /pgconf/hba

    Writes ``pg_hba.conf`` file content.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    POST /pgconf/hba HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-Type: application/json

    {
        "entries":
        [
            {
                "connection": "local",
                "user": "all",
                "database": "all",
                "auth_method": "peer"
            }
        ],
        "new_version": true
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "last_version": "2016-02-11T15:26:19",
        "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
    }


.. http:post:: /pgconf/hba/raw

    Writes ``pg_hba.conf`` file content. Raw mode.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    POST /pgconf/hba/raw HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-Type: application/json

    {
        "content": "local all all md5\r\n ... ",
        "new_version": true
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "last_version": "2016-02-11T15:26:19",
        "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
    }


.. http:delete:: /pgconf/hba

    Remove a version of ``pg_hba.conf`` file.

    :query version: ``pg_hba.conf`` file version to remove. Ex: ``2017-03-06T16:34:07``.
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 404: ``version`` does not exist
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example requests**:

.. sourcecode:: http

    DELETE /pgconf/hba?version=2017-03-06T16:34:07 HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "deleted": true,
        "version": "2016-01-29T08:44:26"
    }


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 404 Not Found
    Server: temboard-agent/0.0.1 Python/2.7.9
    Date: Thu, 11 Feb 2016 09:04:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"error": "Version 2016-01-29T08:46:09 of file /etc/postgresql/9.4/main/pg_hba.conf does not exist."}


.. http:get:: /pgconf/hba/versions

    Get the list of ``pg_hba.conf`` versions.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example requests**:

.. sourcecode:: http

    GET /pgconf/hba/version HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "versions":
        [
            "2016-02-11T18:01:35",
            "2016-02-11T16:43:51",
            "2016-02-11T16:43:36"
        ],
        "filepath": "/etc/postgresql/9.4/main/pg_hba.conf"
    }


.. http:get:: /pgconf/pg_ident

    Get raw content of ``pg_ident.conf`` file

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example requests**:

.. sourcecode:: http

    GET /pgconf/pg_ident HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "content": "# PostgreSQL User Name Maps\r\n# =========================\r\n ... ",
        "filepath": "/etc/postgresql/9.4/main/pg_ident.conf"
    }


.. http:post:: /pgconf/pg_ident

    Write ``pg_ident.conf`` file content. Raw mode.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    POST /pgconf/pg_ident HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-Type: application/json

    {
        "content": "# PostgreSQL User Name Maps\r\n ..."
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "update": true
    }


.. http:get:: /pgconf/hba/options

    Get HBA potential values for each column.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example requests**:

.. sourcecode:: http

    GET /pgconf/hba/options HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "connection": [ "local", "host", "hostssl", "hostnossl" ],
        "database": [ "all", "sameuser", "samerole", "db1" ],
        "user": [ "all", "user1", "+group1" ],
        "auth_method": [ "trust", "reject" ]
    }
