from tornado.ioloop import IOLoop
from multiprocessing.pool import ThreadPool

_worker = None


def new_worker_pool(nb):
    global _workers
    _workers = ThreadPool(nb)


def run_background(func, callback, args=(), kwds={}):
    def _callback(result):
        IOLoop.instance().add_callback(lambda: callback(result))

    _workers.apply_async(func, args, kwds, _callback)


class AsyncResult(object):
    def __init__(self,
                 http_code=0,
                 content_type="application/unknown",
                 data={}):
        self.http_code = http_code
        self.content_type = content_type
        self.data = data


class HTMLAsyncResult(AsyncResult):
    def __init__(self,
                 http_code=0,
                 redirection=None,
                 data={},
                 template_file=None,
                 template_path=None,
                 secure_cookie=None):
        super(HTMLAsyncResult, self).__init__(
            http_code=http_code, content_type="text/html", data=data)
        self.redirection = redirection
        self.template_file = template_file
        self.template_path = template_path
        self.secure_cookie = secure_cookie


class JSONAsyncResult(AsyncResult):
    def __init__(self, http_code=0, data={}, secure_cookie=None):
        super(JSONAsyncResult, self).__init__(
            http_code=http_code, content_type="application/json", data=data)
        self.secure_cookie = secure_cookie


class CSVAsyncResult(AsyncResult):
    def __init__(self, http_code=0, data={}):
        super(CSVAsyncResult, self).__init__(
            http_code=http_code, content_type="text/csv", data=data)
