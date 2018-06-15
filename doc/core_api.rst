.. _core_api:

Core API
========

.. http:post:: /login

    User login

    :reqheader Content-Type: ``application/json``
    :status 200: no error
    :status 404: invalid username or password
    :status 500: internal error
    :status 406: username or password malformed or missing


**Example request**:

.. sourcecode:: http

    POST /login HTTP/1.1
    Content-Type: application/json

    {
        "username": "alice",
        "password": "foo!!"
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:19:48 GMT
    Content-type: application/json

    {"session": "fa452548403ac53f2158a65f5eb6db9723d2b07238dd83f5b6d9ca52ce817b63"}

**Error responses**:

.. sourcecode:: http

    HTTP/1.0 404 Not Found
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:20:33 GMT
    Content-type: application/json

    {"error": "Invalid username/password."}

.. sourcecode:: http

    HTTP/1.0 406 Not Acceptable
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:21:01 GMT
    Content-type: application/json

    {"error": "Parameter 'password' is malformed."}


.. http:get:: /logout

    User logout

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session ID
    :status 500: internal error
    :status 406: session ID malformed


**Example request**:

.. sourcecode:: http

    GET /logout HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:33:19 GMT
    Content-type: application/json

    {"logout": true}


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 401 Unauthorized
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:36:33 GMT
    Content-type: application/json

    {"error": "Invalid session."}


.. sourcecode:: http

    HTTP/1.0 406 Not Acceptable
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:37:23 GMT
    Content-type: application/json

    {"error": "Parameter 'X-Session' is malformed."}


.. http:get:: /discovery

    Get global informations about the environment

    :status 200: no error
    :status 500: internal error


**Example request**:

.. sourcecode:: http

    GET /discover HTTP/1.1


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:33:19 GMT
    Content-type: application/json

    {
        "hostname": "neptune",
        "pg_data": "/var/lib/postgresql/9.4/main",
        "pg_port": 5432,
        "plugins": ["monitoring", "dashboard", "pgconf", "administration", "activity"],
        "memory_size": 8241508352,
        "pg_version": "PostgreSQL 9.4.5 on x86_64-unknown-linux-gnu, compiled by gcc (Ubuntu 4.9.2-10ubuntu13) 4.9.2, 64-bit",
        "cpu": 4
    }

.. http:get:: /profile

    Get current username

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session ID
    :status 500: internal error
    :status 406: session ID malformed


**Example request**:

.. sourcecode:: http

    GET /profile HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:33:19 GMT
    Content-type: application/json

    {
        "username": "alice"
    }


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 401 Unauthorized
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:36:33 GMT
    Content-type: application/json

    {"error": "Invalid session."}


.. sourcecode:: http

    HTTP/1.0 406 Not Acceptable
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:37:23 GMT
    Content-type: application/json

    {"error": "Parameter 'X-Session' is malformed."}


.. http:get:: /notifications

    Get all notifications from the agent.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session ID
    :status 500: internal error
    :status 406: session ID malformed


**Example request**:

.. sourcecode:: http

    GET /notifications HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e


**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:33:19 GMT
    Content-type: application/json

    [
        {"date": "2016-04-11T16:12:38", "username": "alice", "message": "Login"},
        {"date": "2016-04-11T16:02:03", "username": "alice", "message": "Login"},
        {"date": "2016-04-11T15:51:15", "username": "alice", "message": "HBA file version '2016-04-11T15:32:53' removed."},
        {"date": "2016-04-11T15:51:10", "username": "alice", "message": "HBA file version '2016-04-11T15:47:26' removed."},
        {"date": "2016-04-11T15:51:04", "username": "alice", "message": "HBA file version '2016-04-11T15:48:50' removed."},
        {"date": "2016-04-11T15:50:57", "username": "alice", "message": "PostgreSQL reload"},
        {"date": "2016-04-11T15:50:57", "username": "alice", "message": "HBA file updated"},
        {"date": "2016-04-11T15:48:50", "username": "alice", "message": "PostgreSQL reload"}
    ]


**Error responses**:

.. sourcecode:: http

    HTTP/1.0 401 Unauthorized
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:36:33 GMT
    Content-type: application/json

    {"error": "Invalid session."}


.. sourcecode:: http

    HTTP/1.0 406 Not Acceptable
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 12:37:23 GMT
    Content-type: application/json

    {"error": "Parameter 'X-Session' is malformed."}


.. http:get:: /status

    Get informations about the agent

    :status 200: no error
    :status 500: internal error


**Example request**:

.. sourcecode:: http

    GET /status HTTP/1.1


**Example response**:

.. sourcecode:: http


    HTTP/1.0 200 OK
    Server: temboard-agent/2.0+master Python/2.7.5
    Date: Fri, 15 Jun 2018 13:42:57 GMT
    Access-Control-Allow-Origin: *
    Content-type: application/json

    {
        "start_datetime": "2018-06-15T15:42:42",
        "version": "2.0+master",
        "user": "postgres",
        "reload_datetime": "2018-06-15T15:42:42",
        "pid": 32669,
        "configfile": "/etc/temboard-agent/temboard-agent.conf"
    }
