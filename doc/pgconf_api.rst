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
                    "boot_val": "on",
                    "reset_val": "on",
                    "unit": null,
                    "desc": "Starts the autovacuum subprocess.",
                    "name": "autovacuum",
                    "min_val": null,
                    "setting": "off",
                    "setting_raw": "off",
                    "pending_restart": "f"
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
                    "boot_val": "on",
                    "reset_val": "on",
                    "unit": null,
                    "desc": "Starts the autovacuum subprocess. ",
                    "name": "autovacuum",
                    "min_val": null,
                    "setting": "on",
                    "setting_raw": "on",
                    "pending_restart": "f"
                }
            ]
        }
    ]


.. http:get:: /pgconf/configuration/status

    Shows settings waiting for PostgreSQL server restart

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
                "enumvals": null,
                "max_val": 1073741823,
                "vartype": "integer",
                "boot_val": 1024,
                "reset_val": 16384,
                "unit": "8kB",
                "desc": "Sets the number of shared memory buffers used by the server. ",
                "name": "shared_buffers",
                "min_val": 16,
                "setting": 16384,
                "setting_raw": "128MB",
                "pending_restart": "t"
            }
        ],
        "restart_pending": true
    }
