import re
import sys

ROUTES = []
WORKERS = []


def add_route(method, path):
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
        ROUTES.append({
            'http_method': method,
            'root': root,
            'path': path,
            'splitpath': splitpath,
            'module': function.__module__,
            'function': function.__name__})
        return function
    return func_wrapper


def get_routes():
    """
    Returns the routes.
    """
    return ROUTES


def add_worker(name):
    """
    Function decorator for worker name -> worker function mapping.
    """
    def func_wrapper(function):
        global WORKERS
        WORKERS.append({
            'name': name,
            'module': function.__module__,
            'function': function.__name__})
        return function
    return func_wrapper


def get_worker(name):
    """
    Returns the function corresponding to the given worker name.
    """
    for worker in WORKERS:
        if worker['name'] == name:
            return getattr(sys.modules[worker['module']], worker['function'])
    raise Exception("Worker %s not found." % (name,))
