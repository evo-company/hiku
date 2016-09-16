# graph definition

from datetime import datetime

from hiku.graph import Graph, Root, Field

GRAPH = Graph([
    Root([
        Field('now', lambda _: [datetime.now().isoformat()]),
    ]),
])

# test

from hiku.engine import Engine
from hiku.result import denormalize
from hiku.executors.sync import SyncExecutor
from hiku.readers.simple import read

hiku_engine = Engine(SyncExecutor())

def execute(graph, query_string):
    query = read(query_string)
    result = hiku_engine.execute(graph, query)
    return denormalize(graph, result, query)

from tests.base import patch, Mock

_NOW = datetime(2015, 10, 21, 7, 28)

@patch('{}.datetime'.format(__name__))
def test(dt):
    dt.now = Mock(return_value=_NOW)
    result = execute(GRAPH, '[:now]')
    assert result == {'now': '2015-10-21T07:28:00'}

# console

from hiku.console.ui import ConsoleApplication

app = ConsoleApplication(GRAPH, hiku_engine, debug=True)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    http_server = make_server('localhost', 5000, app)
    http_server.serve_forever()
