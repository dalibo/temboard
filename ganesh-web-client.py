import tornado.ioloop
import tornado.web

from ganeshwebui.handlers.base import *
from ganeshwebui.handlers.user import *
from ganeshwebui.handlers.dashboard import *
from ganeshwebui.handlers.administration import *
from ganeshwebui.handlers.activity import *

application = tornado.web.Application([
        (r"/", BaseHandler),
        (r"/server/(.*)/([0-9]{1,5})/administration/configuration$", AdminConfigurationHandler),
        (r"/server/(.*)/([0-9]{1,5})/administration/configuration/category/(.+)$", AdminConfigurationHandler),
        (r"/server/(.*)/([0-9]{1,5})/administration/hba", AdminHBAHandler),
        (r"/server/(.*)/([0-9]{1,5})/administration/pg_ident", AdminPGIdentHandler),
        (r"/server/(.*)/([0-9]{1,5})/activity", ActivityHandler),
        (r"/server/(.*)/([0-9]{1,5})/login", LoginHandler),
        (r"/server/(.*)/([0-9]{1,5})/dashboard", DashboardHandler),
        (r"/proxy/(.*)/([0-9]{1,5})/dashboard", DashboardProxyHandler),
        (r"/proxy/(.*)/([0-9]{1,5})/activity", ActivityProxyHandler),
        (r"/proxy/(.*)/([0-9]{1,5})/activity/kill", ActivityKillProxyHandler),
        (r"/proxy/(.*)/([0-9]{1,5})/administration/control", AdminControlProxyHandler),
        (r"/proxy/(.*)/([0-9]{1,5})/administration/configuration", AdminConfigurationProxyHandler),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/css'}),
        (r"/codemirror/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/codemirror'}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/js'}),
        (r"/imgs/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/imgs'}),
        (r"/fonts/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/fonts'})
    ],
    cookie_secret="7ee98be2cbea98a466739f3130955655d4a60e3bc6dc5c34a28acae8346f02c1",
    template_path="ganeshwebui/templates"
)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
