from wsgiref.simple_server import make_server

from hiku.console.ui import ConsoleApplication

from tests.test_source_sqlalchemy import TestSourceSQL, ENV


if __name__ == '__main__':
    test = TestSourceSQL(methodName='testManyToOne')
    test.setUp()
    app = ConsoleApplication(ENV, test.engine)
    http_server = make_server('localhost', 5000, app)
    http_server.serve_forever()
