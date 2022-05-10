import functools
import logging
import json

from bottle import Bottle, HTTPError, HTTPResponse, Response, request, response

from .. import errors
from ..tools import JSONEncoder


logger = logging.getLogger(__name__)


def create_app(temboard):
    Response.default_content_type = 'text/plain'
    app = CustomBottle(autojson=False)
    app.temboard = temboard
    app.install(ErrorPlugin())
    app.add_hook('before_request', before_request_log)
    app.add_hook('after_request', after_request_log)
    app.install(JSONPlugin())
    app.install(ErrorPlugin())
    return app


class CustomBottle(Bottle):
    def default_error_handler(self, res):
        # Skip HTML template.
        return res.body


def before_request_log():
    logger.debug("New web request: %s %s", request.method, request.path)


def after_request_log():
    if response.status_code > 500:
        logmethod = logger.error
    else:
        logmethod = logger.info
    logmethod("%s %s %s", request.method, request.path, response.status)


class ErrorPlugin(object):
    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*a, **kw):
            try:
                response = callback(*a, **kw)
            except HTTPError as e:
                if isinstance(e.body, str):
                    e.body = {'error': e.body}
                logger.debug("Error: %s.", e.body)
                raise
            except HTTPResponse:
                raise
            except errors.HTTPError as e:
                # Callback may call other function raising legacy HTTPError.
                response = HTTPResponse({'error': str(e)}, e.code)
                logger.debug("Error: %s.", response.body)
            except Exception:
                logger.exception("Unhandled error:")
                response = HTTPResponse({'error': 'Internal error.'}, 500)

            return response
        return wrapper


class JSONPlugin(object):
    # Bottle jsonify only dict. JSON Array was a security issue for some
    # browser.
    def apply(self, callback, route):
        @functools.wraps(callback)
        def wrapper(*a, **kw):
            res = callback(*a, **kw)
            body = res.body if isinstance(res, HTTPResponse) else res

            if not isinstance(body, (dict, list)):
                return res

            body = json.dumps(body, cls=JSONEncoder)
            if isinstance(res, HTTPResponse):
                res.body = body
            else:
                res = HTTPResponse(body)

            res.headers['Content-Type'] = 'application/json'

            return res
        return wrapper
