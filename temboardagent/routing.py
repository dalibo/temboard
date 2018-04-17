import re
import logging

ROUTES = []
WORKERS = []

logger = logging.getLogger(__name__)


def add_route(method, path, check_session=True):
    """
    Function decorator for HTTP method/path -> API function mapping.
    """
    def func_wrapper(function):
        global ROUTES
        splitpath = []
        elts = path.split('/')
        pos = 0
        root = None
        # Seeking for regexp in the path, because we need to compile it.
        for elt in elts:
            if len(elt) == 0:
                continue
            # regexp have to start with a ( end is terminated by a ).
            if elt[0] == '(' and elt[-1] == ')':
                # Append it compiled.
                splitpath.append(re.compile(elt))
            # string case
            else:
                if pos == 0:
                    root = elt
                splitpath.append(elt)
            pos += 1
        # A path can't start with a regexp.
        if root is None:
            raise Exception("Wrong route format.")
        ROUTES.append(dict(
            http_method=method,
            root=root,
            path=path,
            splitpath=splitpath,
            module=function.__module__,
            function=function.__name__,
            check_session=check_session,
        ))
        return function
    return func_wrapper


def get_routes():
    """
    Returns the routes.
    """
    return ROUTES
