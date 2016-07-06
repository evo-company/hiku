from wsgiref.simple_server import make_server

from hiku.console.ui import ConsoleApplication

from tests.test_source_sqlalchemy import TestSourceSQL, GRAPH


if __name__ == '__main__':
    test = TestSourceSQL(methodName='testManyToOne')
    test.setUp()
    app = ConsoleApplication(GRAPH, test.engine, debug=True)
    http_server = make_server('localhost', 5000, app)
    http_server.serve_forever()
