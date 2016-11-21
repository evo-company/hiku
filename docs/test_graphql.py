# prerequisites
from datetime import datetime as _datetime

from tests.base import patch, Mock

_NOW = _datetime(2015, 10, 21, 7, 28)

# example
from datetime import datetime

from hiku.graph import Graph, Root, Field
from hiku.engine import Engine
from hiku.result import denormalize
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import read

GRAPH = Graph([
    Root([
        Field('now', None, lambda _: [datetime.now().isoformat()]),
    ]),
])

hiku_engine = Engine(SyncExecutor())

@patch('{}.datetime'.format(__name__))
def test(dt):
    dt.now = Mock(return_value=_NOW)

    query = read('{ now }')
    result = hiku_engine.execute(GRAPH, query)
    simple_result = denormalize(GRAPH, result, query)
    assert simple_result == {'now': '2015-10-21T07:28:00'}
