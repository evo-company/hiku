import pytest
from hiku.graph import Graph

from hiku.query import Node, Field, Link
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.endpoint import denormalize_entities
from hiku.federation.engine import Engine
from hiku.federation.validate import validate
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import read

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH,
)


def execute(query: Node, graph: Graph, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query, ctx=ctx)


async def execute_async(query: Node, graph: Graph, ctx=None):
    engine = Engine(AsyncIOExecutor())
    return await engine.execute(graph, query, ctx=ctx)


ENTITIES_QUERY = {
    'query': """
        query($representations:[_Any!]!) {
            _entities(representations:$representations) {
                ...on Cart {
                    status { id title }
                }
            }
        }
        """,
    'variables': {
        'representations': [
            {'__typename': 'Cart', 'id': 1},
            {'__typename': 'Cart', 'id': 2},
        ]
    }
}


SDL_QUERY = Node(fields=[
    Link('_service', Node(fields=[Field('sdl')]))
])


def test_validate_entities_query():
    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    errors = validate(GRAPH, query)
    assert errors == []


def test_execute_sync_executor():
    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    result = execute(query, GRAPH)
    data = denormalize_entities(
        GRAPH,
        query,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == data


@pytest.mark.asyncio
async def test_execute_async_executor():
    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    result = await execute_async(query, ASYNC_GRAPH)
    data = denormalize_entities(
        GRAPH,
        query,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == data
