.. _administration_api:

Administration plugin API
=========================

.. http:post:: /administration/control

    Control PostgreSQL server. Supported actions are ``start``, ``stop``, ``restart`` and ``reload``.

    :reqheader X-Session: Session ID
    :status 200: no error
    :status 401: invalid session
    :status 500: internal error
    :status 406: header or parameter is malformed.


**Example request**:

.. sourcecode:: http

    POST /administration/control HTTP/1.1
    X-Session: 3b28ed94743e3ada57b217bbf9f36c6d1eb45e669a1ab693e8ca7ac3bd070b9e
    Content-Type: application/json

    {
        "action": "restart"
    }

**Example response**:

.. sourcecode:: http

    HTTP/1.0 200 OK
    Server: temboard-agent/0.0.1 Python/2.7.8
    Date: Wed, 22 Apr 2015 09:57:52 GMT
    Content-type: application/json

    {
        "action": "restart",
        "state": "ok"
    }


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

    {"error": "Parameter 'action' is malformed."}
