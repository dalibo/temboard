.. _maintenance_api:

Maintenance API
===============

.. http:get:: /maintenance

    Get information about the instance and its databases

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 10:21:44 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "databases": [
            {
                "datname": "postgres",
                "indexes_bloat_bytes": 335872.0,
                "indexes_bloat_size": "328 kB",
                "indexes_bytes": 3162112.0,
                "indexes_size": "3088 kB",
                "n_indexes": 115.0,
                "n_tables": 69.0,
                "tables_bloat_bytes": 49152.0,
                "tables_bloat_size": "48 kB",
                "tables_bytes": 2957312.0,
                "tables_size": "2888 kB",
                "toast_bytes": 679936.0,
                "toast_size": "664 kB",
                "total_bytes": 7788007,
                "total_size": "7605 kB"
            }
        ],
        "instance": {
            "total_bytes": 7788007.0,
            "total_size": "7605 kB"
        }
    }

.. http:get:: /maintenance/<database_name>

    Get information about one database

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 10:24:15 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "schemas": [
            {
                "indexes_bloat_bytes": null,
                "indexes_bloat_size": null,
                "indexes_bytes": 0,
                "indexes_size": null,
                "n_indexes": 0,
                "n_tables": 7,
                "name": "information_schema",
                "tables_bloat_bytes": 0.0,
                "tables_bloat_size": "0 bytes",
                "tables_bytes": 98304,
                "tables_size": "96 kB",
                "toast_bytes": 57344.0,
                "toast_size": "56 kB",
                "total_bytes": 352256,
                "total_size": "344 kB"
            },
            {
                "indexes_bloat_bytes": 335872.0,
                "indexes_bloat_size": "328 kB",
                "indexes_bytes": 3219456,
                "indexes_size": "3144 kB",
                "n_indexes": 115,
                "n_tables": 62,
                "name": "pg_catalog",
                "tables_bloat_bytes": 49152.0,
                "tables_bloat_size": "48 kB",
                "tables_bytes": 2940928,
                "tables_size": "2872 kB",
                "toast_bytes": 630784.0,
                "toast_size": "616 kB",
                "total_bytes": 8003584,
                "total_size": "7816 kB"
            },
            {
                "indexes_bloat_bytes": 16384.0,
                "indexes_bloat_size": "16 kB",
                "indexes_bytes": 180224,
                "indexes_size": "176 kB",
                "n_indexes": 3,
                "n_tables": 3,
                "name": "public",
                "tables_bloat_bytes": 16384.0,
                "tables_bloat_size": "16 kB",
                "tables_bytes": 352256,
                "tables_size": "344 kB",
                "toast_bytes": 24576.0,
                "toast_size": "24 kB",
                "total_bytes": 557056,
                "total_size": "544 kB"
            }
        ],
        "total_bytes": 8492519,
        "total_size": "8293 kB"
    }

.. http:get:: /maintenance/<database_name>/schema/<schema_name>

    Get information about one schema

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/schema/public HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http


    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 10:38:45 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "indexes": [
            {
                "bloat_bytes": 8192.0,
                "bloat_size": "8192 bytes",
                "def": "CREATE UNIQUE INDEX city_pkey ON public.city USING btree (id)",
                "idx_tup_fetch": 0,
                "idx_tup_read": 0,
                "indexrelname": "city_pkey",
                "indisunique": true,
                "name": "city_pkey",
                "number_of_columns": 1,
                "scans": 0,
                "tablename": "city",
                "tablespace": null,
                "total_bytes": 114688,
                "total_size": "112 kB",
                "type": "btree"
            },
            {
                "bloat_bytes": 0.0,
                "bloat_size": "0 bytes",
                "def": "CREATE UNIQUE INDEX country_pkey ON public.country USING btree (code)",
                "idx_tup_fetch": 0,
                "idx_tup_read": 0,
                "indexrelname": "country_pkey",
                "indisunique": true,
                "name": "country_pkey",
                "number_of_columns": 1,
                "scans": 0,
                "tablename": "country",
                "tablespace": null,
                "total_bytes": 16384,
                "total_size": "16 kB",
                "type": "btree"
            },
            {
                "bloat_bytes": 8192.0,
                "bloat_size": "8192 bytes",
                "def": "CREATE UNIQUE INDEX countrylanguage_pkey ON public.countrylanguage USING btree (countrycode, language)",
                "idx_tup_fetch": 0,
                "idx_tup_read": 0,
                "indexrelname": "countrylanguage_pkey",
                "indisunique": true,
                "name": "countrylanguage_pkey",
                "number_of_columns": 2,
                "scans": 0,
                "tablename": "countrylanguage",
                "tablespace": null,
                "total_bytes": 49152,
                "total_size": "48 kB",
                "type": "btree"
            }
        ],
        "size": "544 kB",
        "tables": [
            {
                "bloat_bytes": 16384.0,
                "bloat_size": "16 kB",
                "index_bloat_bytes": 8192.0,
                "index_bloat_size": "8192 bytes",
                "index_bytes": 114688,
                "index_size": "112 kB",
                "n_indexes": 1,
                "name": "city",
                "row_estimate": 4079.0,
                "table_bytes": 262144,
                "table_size": "256 kB",
                "toast_bytes": 8192,
                "toast_size": "8192 bytes",
                "total_bytes": 385024,
                "total_size": "376 kB"
            },
            {
                "bloat_bytes": 0.0,
                "bloat_size": "0 bytes",
                "index_bloat_bytes": 0.0,
                "index_bloat_size": "0 bytes",
                "index_bytes": 16384,
                "index_size": "16 kB",
                "n_indexes": 1,
                "name": "country",
                "row_estimate": 239.0,
                "table_bytes": 40960,
                "table_size": "40 kB",
                "toast_bytes": 8192,
                "toast_size": "8192 bytes",
                "total_bytes": 65536,
                "total_size": "64 kB"
            },
            {
                "bloat_bytes": 0.0,
                "bloat_size": "0 bytes",
                "index_bloat_bytes": 8192.0,
                "index_bloat_size": "8192 bytes",
                "index_bytes": 49152,
                "index_size": "48 kB",
                "n_indexes": 1,
                "name": "countrylanguage",
                "row_estimate": 984.0,
                "table_bytes": 49152,
                "table_size": "48 kB",
                "toast_bytes": 8192,
                "toast_size": "8192 bytes",
                "total_bytes": 106496,
                "total_size": "104 kB"
            }
        ],
        "total_bytes": 557056
    }

.. http:get:: /maintenance/<database_name>/schema/<schema_name>/table/<table_name>

    Get information about one table

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/schema/public/table/country HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 10:40:48 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "analyze_count": 1,
        "autoanalyze_count": 1,
        "autovacuum_count": 0,
        "bloat_bytes": 0.0,
        "bloat_size": "0 bytes",
        "fillfactor": 100,
        "idx_scan": 0,
        "idx_tup_fetch": 0,
        "index_bloat_bytes": 0.0,
        "index_bloat_size": "0 bytes",
        "index_bytes": 16384,
        "index_size": "16 kB",
        "indexes": [
            {
                "bloat_bytes": 0.0,
                "bloat_size": "0 bytes",
                "def": "CREATE UNIQUE INDEX country_pkey ON public.country USING btree (code)",
                "idx_tup_fetch": 0,
                "idx_tup_read": 0,
                "indexrelname": "country_pkey",
                "indisunique": true,
                "name": "country_pkey",
                "number_of_columns": 1,
                "scans": 0,
                "tablename": "country",
                "tablespace": null,
                "total_bytes": 16384,
                "total_size": "16 kB",
                "type": "btree"
            }
        ],
        "last_analyze": "2019-03-22 10:37:19.577101+00",
        "last_autoanalyze": "2019-03-22 10:37:44.297278+00",
        "last_autovacuum": null,
        "last_vacuum": null,
        "n_dead_tup": 0,
        "n_live_tup": 239,
        "n_mod_since_analyze": 0,
        "n_tup_del": 0,
        "n_tup_hot_upd": 0,
        "n_tup_ins": 239,
        "n_tup_upd": 0,
        "name": "country",
        "relid": "16432",
        "relname": "country",
        "row_estimate": 239.0,
        "schemaname": "public",
        "seq_scan": 3,
        "seq_tup_read": 717,
        "table_bytes": 40960,
        "table_size": "40 kB",
        "toast_bytes": 8192,
        "toast_size": "8192 bytes",
        "total_bytes": 65536,
        "total_size": "64 kB",
        "vacuum_count": 0
    }

.. http:post:: /maintenance/<database_name>/vacuum

    Launch a VACUUM on the database

    The VACUUM can be scheduled if `datetime` is provided.

    The mode parameter can be a combination of 'full', 'freeze' or 'analyze'.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'mode' is malformed or Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/vacuum HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "mode": "full,analyze",
        "datetime": "2019-03-22T12:24:39Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 11:08:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "239cd9a0"
    }

.. http:post:: /maintenance/<database_name>/schema/<schema_name>/table/<table_name>/vacuum

    Launch a VACUUM on the table.

    The VACUUM can be scheduled if `datetime` is provided.

    The mode parameter can be a combination of 'full', 'freeze' or 'analyze'.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'mode' is malformed or Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/schema/public/table/country/vacuum HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "mode": "full,analyze",
        "datetime": "2019-03-22T12:24:39Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 11:08:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "229cc880"
    }

.. http:get:: /maintenance/<database_name>/schema/<schema_name>/table/<table_name>/vacuum/scheduled

    Get the id of the scheduled VACUUM operations for the given table.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/schema/public/table/country/vacuum/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "9ce6426b",
            "index": null,
            "mode": "full",
            "schema": "public",
            "status": "todo",
            "table": "country"
        }
    ]

.. http:delete:: /maintenance/vacuum/<operation_id>

    Cancel the given VACUUM operation.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    DELETE /maintenance/vacuum/9ce6426b HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 15:01:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"response": "ok"}

.. http:get:: /maintenance/vacuum/scheduled

    Get the id of all the scheduled VACUUM operations.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/vacuum/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "9ce6426b",
            "index": null,
            "mode": "full",
            "schema": "public",
            "status": "todo",
            "table": "country"
        },
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "785b82c6",
            "index": null,
            "mode": "full",
            "schema": "public",
            "status": "todo",
            "table": "city"
        }
    ]

.. http:get:: /maintenance/<database_name>/vacuum/scheduled

    Get the id of all the scheduled VACUUM operations.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/vacuum/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "9ce6426b",
            "index": null,
            "mode": "full",
            "schema": "public",
            "status": "todo",
            "table": "country"
        },
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "785b82c6",
            "index": null,
            "mode": "full",
            "schema": "public",
            "status": "todo",
            "table": "city"
        }
    ]

.. http:post:: /maintenance/<database_name>/analyze

    Launch a ANALYZE on the database.

    The ANALYZE can be scheduled if `datetime` is provided.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/analyze HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "datetime": "2019-03-23T11:28:00Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 15:12:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "1ac59a5e"
    }

.. http:post:: /maintenance/<database_name>/schema/<schema_name>/table/<table_name>/analyze

    Launch a ANALYZE on the table.

    The ANALYZE can be scheduled if `datetime` is provided.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/schema/public/table/country/analyze HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "datetime": "2019-03-23T11:28:00Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 15:12:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "1045055e"
    }

.. http:get:: /maintenance/<database_name>/analyze/scheduled

    Get the id of the scheduled ANALYZE operations for the given database

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/analyze/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "1045055e",
            "index": null,
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": "country"
        }
    ]

.. http:get:: /maintenance/<database_name>/schema/<schema_name>/table/<table_name>/analyze/scheduled

    Get the id of the scheduled ANALYZE operations for the given table.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/schema/public/table/country/analyze/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "1045055e",
            "index": null,
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": "country"
        }
    ]

.. http:delete:: /maintenance/analyze/<operation_id>

    Cancel the given ANALYZE operation.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    DELETE /maintenance/analyze/1045055e HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 15:01:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"response": "ok"}

.. http:get:: /maintenance/analyze/scheduled

    Get the id of all the scheduled ANALYZE operations.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/analyze/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "1847795b",
            "index": null,
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": "country"
        },
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "1045055e",
            "index": null,
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": "city"
        }
    ]

.. http:post:: /maintenance/<database_name>/reindex

    Launch a REINDEX on the database.

    The REINDEX can be scheduled if `datetime` is provided.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/reindex HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "datetime": "2019-03-22T12:24:39Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 11:08:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "7f377004"
    }

.. http:post:: /maintenance/<database_name>/schema/<schema_name>/table/<table_name>/reindex

    Launch a REINDEX on the table.

    The REINDEX can be scheduled if `datetime` is provided.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/schema/public/table/country/reindex HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "datetime": "2019-03-22T12:24:39Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 11:08:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "7f377004"
    }

.. http:post:: /maintenance/<database_name>/schema/<schema_name>/index/<index_name>/reindex

    Launch a REINDEX on the index.

    The REINDEX can be scheduled if `datetime` is provided.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed, Parameter 'datetime' is maformed.


**Example request**:

.. sourcecode:: http

    POST /maintenance/postgres/schema/public/index/country_pkey/reindex HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-type: application/json

    {
        "datetime": "2019-03-22T12:24:39Z"
    }


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 11:08:02 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "id": "7f377004"
    }

.. http:get:: /maintenance/<database_name>/reindex/scheduled

    Get the id of the scheduled REINDEX operations for the given database.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/reindex/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "7f377004",
            "index": "country_pkey",
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": null
        },
        {
            "datetime": "2019-03-24T10:32:00Z",
            "dbname": "postgres",
            "id": "7a3cae05",
            "index": null,
            "mode": null,
            "schema": null,
            "status": "todo",
            "table": null
        }
    ]

.. http:get:: /maintenance/<database_name>/schema/<schema_name>/reindex/scheduled

    Get the id of the scheduled REINDEX operations for the given schema.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.

.. http:get:: /maintenance/<database_name>/schema/<schema_name>/<index_name>/table/<table_name>/reindex/scheduled

    Get the id of the scheduled REINDEX operations for the given schema.
    Alias for `/maintenance/<database_name>/schema/<schema_name>/reindex/scheduled` (See below).
    Note: does not filter on table.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.

.. http:get:: /maintenance/<database_name>/schema/<schema_name>/reindex/scheduled

    Get the id of the scheduled REINDEX operations for the given schema.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/postgres/schema/public/reindex/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "7f377004",
            "index": "country_pkey",
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": null
        }
    ]

.. http:delete:: /maintenance/reindex/<operation_id>

    Cancel the given REINDEX operation.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    DELETE /maintenance/reindex/7f377004 HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 15:01:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {"response": "ok"}

.. http:get:: /maintenance/reindex/scheduled

    Get the id of all the scheduled REINDEX operations.

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /maintenance/reindex/scheduled HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/4.0+master Python/3.7.2
    Date: Fri, 22 Mar 2019 14:39:01 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    [
        {
            "datetime": "2019-03-23T11:28:00Z",
            "dbname": "postgres",
            "id": "7f377004",
            "index": "country_pkey",
            "mode": null,
            "schema": "public",
            "status": "todo",
            "table": null
        }
    ]
