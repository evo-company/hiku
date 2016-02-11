from wsgiref.simple_server import make_server

from hiku.console.ui import ConsoleResponse, QueryResponse, DocResponse

from tests.test_source_sqlalchemy import TestSourceSQL, ENV


class Application(object):

    def __init__(self, engine):
        self.console_response = ConsoleResponse()
        self.doc_response = DocResponse(ENV)
        self.query_response = QueryResponse(engine, ENV)

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET':
            if environ['PATH_INFO'] in ('/', ''):
                return self.console_response(environ, start_response)
            elif environ['PATH_INFO'] == '/doc':
                return self.doc_response(environ, start_response)
            else:
                start_response('404 Not Found', [])
                return [b'']
        elif environ['REQUEST_METHOD'] == 'POST':
            return self.query_response(environ, start_response)
        else:
            start_response('405 Method Not Allowed', [])
            return [b'']


if __name__ == '__main__':
    test = TestSourceSQL()
    test.setUp()
    app = Application(test.engine)
    http_server = make_server('localhost', 5000, app)
    http_server.serve_forever()
