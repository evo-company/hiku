import pytest

from hiku.context import create_execution_context
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


def execute(graph, query: Node, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute_query(graph, query, ctx=ctx)


async def execute_async_executor(graph, query: Node, ctx=None):
    engine = Engine(AsyncIOExecutor())
    return await engine.execute_query(graph, query, ctx=ctx)


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
QUERY = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])


SDL_QUERY = Node(fields=[
    Link('_service', Node(fields=[Field('sdl')]))
])


def test_validate_entities_query():
    errors = validate(GRAPH, QUERY)
    assert errors == []


def test_execute_sync_executor():
    result = execute(GRAPH, QUERY, {})
    data = denormalize_entities(
        GRAPH,
        QUERY,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == data


@pytest.mark.asyncio
async def test_execute_async_executor():
    result = await execute_async_executor(ASYNC_GRAPH, QUERY, {})
    data = denormalize_entities(
        GRAPH,
        QUERY,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == data
