import tornado.ioloop
import tornado.web
from ganeshwebui.handlers import *

application = tornado.web.Application([
    (r"/", BaseHandler),
    (r"/server/(.*)/([0-9]{1,5})/login", LoginHandler),
    (r"/server/(.*)/([0-9]{1,5})/dashboard", DashboardHandler),
    (r"/proxy/(.*)/([0-9]{1,5})/dashboard", DashboardProxyHandler),
    (r"/css/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/css'}),
    (r"/js/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/js'}),
    (r"/fonts/(.*)", tornado.web.StaticFileHandler, {'path': 'ganeshwebui/static/fonts'})
],
cookie_secret="7ee98be2cbea98a466739f3130955655d4a60e3bc6dc5c34a28acae8346f02c1",
template_path="ganeshwebui/templates"
)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
