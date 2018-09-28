# prerequisites
from datetime import datetime as _datetime

import pytest

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
def test_query(dt):
    dt.now = Mock(return_value=_NOW)

    query = read('{ now }')
    result = hiku_engine.execute(GRAPH, query)
    simple_result = denormalize(GRAPH, result, query)
    assert simple_result == {'now': '2015-10-21T07:28:00'}


def test_sync_introspection():
    graph = GRAPH

    from hiku.graph import apply
    from hiku.introspection.graphql import GraphQLIntrospection

    graph = apply(graph, [GraphQLIntrospection(graph)])

    query = read('{ __typename }')
    result = hiku_engine.execute(graph, query)
    simple_result = denormalize(graph, result, query)
    assert simple_result == {'__typename': 'Root'}


@pytest.mark.asyncio
async def test_async_introspection(event_loop):
    from hiku.executors.asyncio import AsyncIOExecutor
    from hiku.introspection.graphql import MakeAsync

    graph = MakeAsync().visit(GRAPH)
    async_hiku_engine = Engine(AsyncIOExecutor(event_loop))

    from hiku.graph import apply
    from hiku.introspection.graphql import AsyncGraphQLIntrospection

    graph = apply(graph, [AsyncGraphQLIntrospection(graph)])

    query = read('{ __typename }')
    result = await async_hiku_engine.execute(graph, query)
    simple_result = denormalize(graph, result, query)
    assert simple_result == {'__typename': 'Root'}
