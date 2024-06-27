import logging

from bottle import HTTPError, HTTPResponse, default_app, get, post, request, response

from ..notification import NotificationMgmt
from ..toolkit.signing import InvalidSignature, canonicalize_request, verify_v1

logger = logging.getLogger(__name__)


@get("/error/<error_code:int>", skip=["signature"])
def get_error(error_code):
    if error_code < 400:
        raise HTTPResponse("HTTPResponse raised", error_code)
    elif error_code < 500:
        raise HTTPError(error_code, "HTTPError raised")
    else:
        raise Exception("This is an Exception %s" % error_code)


@get("/discover", skip=["signature"])
def get_discover():
    app = default_app().temboard
    discover = app.discover.ensure_latest().copy()
    discover["signature_status"] = "enabled"

    signature = request.headers.get("x-temboard-signature")
    if signature:
        crequest = canonicalize_request(request.method, request.path, request.headers)
        try:
            if not signature.startswith("v1:"):
                raise InvalidSignature("Unsupported signature version.")
            signature = signature[3:]

            verify_v1(app.config.signing_key, signature, crequest)
            discover["signature_status"] = "valid"
        except InvalidSignature:
            discover["signature_status"] = "invalid"

    response.set_header("ETag", app.discover.etag)
    return discover


@post("/discover")
def post_discover(pgconn):
    app = default_app().temboard
    data = app.discover.refresh(pgconn).copy()
    # POST endpoint does not bypass signature verification.
    data["signature_status"] = "valid"
    response.set_header("ETag", app.discover.etag)
    return data


@get("/notifications")
def notifications():
    config = default_app().temboard.config
    return list(NotificationMgmt.get_last_n(config, -1))


@get("/status", skip=["signature"])
def get_status(pgconn):
    app = default_app().temboard
    response.set_header("X-TemBoard-Discover-ETag", app.discover.etag)
    return app.status.get(pgconn)
