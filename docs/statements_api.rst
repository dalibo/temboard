.. _statements_api:

Statements plugin API
=====================

.. http:get:: /statements

    Get latest statistics of executed SQL statements

    :query key: Agent's key for authentication (optional)
    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 404: pg_stat_statements not enabled on the database
    :status 500: internal error
    :status 406: header ``X-Session`` is malformed.


**Example request**:

.. sourcecode:: http

    GET /statements HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e

    {
      "snapshot_datetime": "2020-03-17 17:31:25.0929+01",
      "data": [
        {
          "rolname": "postgres",
          "datname ": "bench",
          "userid": 987342,
          "dbid": 8737,
          "queryid": 125206108,
          "query": "SELECT pg_sleep($1)",
          "calls": 1,
          "total_time": 1001.583008,
          "min_time": 1001.583008,
          "max_time": 1001.583008,
          "mean_time": 1001.583008,
          "stddev_time": 0,
          "rows": 1,
          "shared_blks_hit": 0,
          "shared_blks_read": 0,
          "shared_blks_dirtied": 0,
          "shared_blks_written": 0,
          "local_blks_hit": 0,
          "local_blks_read": 0,
          "local_blks_dirtied": 0,
          "local_blks_written": 0,
          "temp_blks_read ": 0,
          "temp_blks_written": 0,
          "blk_read_time": 0,
          "blk_write_time": 0
        }
      ]
    }
