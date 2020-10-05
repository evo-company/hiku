import pytest

from hiku.graph import Graph, Root, Field
from hiku.types import String
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import read
from hiku.endpoint.graphql import _StripQuery, GraphQLEndpoint
from hiku.endpoint.graphql import BatchGraphQLEndpoint, AsyncGraphQLEndpoint
from hiku.endpoint.graphql import AsyncBatchGraphQLEndpoint
from hiku.executors.asyncio import AsyncIOExecutor


def test_strip():
    query = read("""
    query {
        __typename
        foo {
            __typename
            bar {
                __typename
                baz
            }
        }
    }
    """)
    assert _StripQuery().visit(query) == read("""
    query {
        foo {
            bar {
                baz
            }
        }
    }
    """)


@pytest.fixture(name='sync_graph')
def sync_graph_fixture():
    def answer(fields):
        return ['42' for _ in fields]
    return Graph([Root([Field('answer', String, answer)])])


@pytest.fixture(name='async_graph')
def async_graph_fixture():
    async def answer(fields):
        return ['42' for _ in fields]
    return Graph([Root([Field('answer', String, answer)])])


def test_endpoint(sync_graph):
    endpoint = GraphQLEndpoint(Engine(SyncExecutor()), sync_graph)
    result = endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}


def test_batch_endpoint(sync_graph):
    endpoint = BatchGraphQLEndpoint(Engine(SyncExecutor()), sync_graph)

    assert endpoint.dispatch([]) == []

    result = endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}

    batch_result = endpoint.dispatch([
        {'query': '{answer}'},
        {'query': '{__typename}'},
    ])
    assert batch_result == [
        {'data': {'answer': '42'}},
        {'data': {'__typename': 'Query'}},
    ]


@pytest.mark.asyncio
async def test_async_endpoint(async_graph):
    endpoint = AsyncGraphQLEndpoint(Engine(AsyncIOExecutor()), async_graph)
    result = await endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}


@pytest.mark.asyncio
async def test_async_batch_endpoint(async_graph):
    endpoint = AsyncBatchGraphQLEndpoint(Engine(AsyncIOExecutor()), async_graph)

    assert await endpoint.dispatch([]) == []

    result = await endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}

    batch_result = await endpoint.dispatch([
        {'query': '{answer}'},
        {'query': '{__typename}'},
    ])
    assert batch_result == [
        {'data': {'answer': '42'}},
        {'data': {'__typename': 'Query'}},
    ]
