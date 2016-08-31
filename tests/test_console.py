import json
from io import BytesIO
from wsgiref.util import setup_testing_defaults

from hiku.engine import Engine
from hiku.console.ui import ConsoleApplication
from hiku.executors.sync import SyncExecutor

from .test_source_sqlalchemy import GRAPH, SA_ENGINE, TestSourceSQL

engine = Engine(SyncExecutor())


def request(app, method, path_info, script_name='', payload=None):
    env = {'REQUEST_METHOD': method, 'SCRIPT_NAME': script_name,
           'PATH_INFO': path_info}
    if payload is not None:
        env['wsgi.input'] = BytesIO(payload)
        env['CONTENT_LENGTH'] = len(payload)

    meta = []

    def start_response(status, headers, exc_info=None):
        meta.extend((status, headers, exc_info))

    setup_testing_defaults(env)
    app_iter = app(env, start_response)
    assert len(meta) == 3 and meta[2] is None
    return meta[0], meta[1], b''.join(app_iter)


def test_ui():
    app = ConsoleApplication(GRAPH, engine, debug=True)
    status, headers, _ = request(app, 'GET', '/')
    assert status == '200 OK'
    assert ('Content-Type', 'text/html') in headers


def test_docs():
    app = ConsoleApplication(GRAPH, engine, debug=True)
    status, headers, content = request(app, 'GET', '/docs')
    assert status == '200 OK'
    assert content.startswith(b'type')


def test_query():
    test = TestSourceSQL(methodName='testManyToOne')
    test.setUp()

    app = ConsoleApplication(GRAPH, engine, {SA_ENGINE: test.sa_engine},
                             debug=True)
    query = b'[{:bar-list [:name :type {:foo-s [:name :count]}]}]'

    status, headers, content = request(app, 'POST', '/', payload=query)
    assert status == '200 OK'
    assert ('Content-Type', 'application/json') in headers
    result = json.loads(content.decode('utf-8'))
    assert 'bar-list' in result
