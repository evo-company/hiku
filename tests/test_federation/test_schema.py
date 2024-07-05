import pytest

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.schema import Schema
from hiku.federation.engine import Engine
from hiku.executors.sync import SyncExecutor

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH,
)


def execute_schema_v1(query):
    return Schema(
        Engine(SyncExecutor()),
        GRAPH,
        federation_version=1,
    ).execute_sync(query)


def execute_schema_v2(query):
    return Schema(
        Engine(SyncExecutor()),
        GRAPH,
    ).execute_sync(query)


async def execute_async_schema_v1(query):
    return await Schema(
        Engine(AsyncIOExecutor()),
        ASYNC_GRAPH,
        federation_version=1,
    ).execute(query)


async def execute_async_schema_v2(query):
    return await Schema(
        Engine(AsyncIOExecutor()),
        ASYNC_GRAPH,
    ).execute(query)


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

SDL_QUERY = {
    'query': "query __ApolloGetServiceDefinition__ { _service { sdl } }",
    'variables': None,
    'operationName': '__ApolloGetServiceDefinition__',
}


@pytest.mark.parametrize('execute', [
    execute_schema_v1,
    execute_schema_v2
])
def test_fetch_sdl(execute):
    result = execute(SDL_QUERY)
    assert result['data']['_service']['sdl'] is not None


@pytest.mark.parametrize('execute', [
    execute_async_schema_v1,
    execute_async_schema_v2
])
@pytest.mark.asyncio
async def test_fetch_sdl_async(execute):
    result = await execute(SDL_QUERY)
    assert result['data']['_service']['sdl'] is not None


@pytest.mark.parametrize('execute', [
    execute_schema_v1,
    execute_schema_v2
])
def test_execute_sync(execute):
    result = execute(ENTITIES_QUERY)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result['data']['_entities']


@pytest.mark.asyncio
@pytest.mark.parametrize('execute', [
    execute_async_schema_v1,
    execute_async_schema_v2
])
async def test_execute_async(execute):
    result = await execute(ENTITIES_QUERY)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result['data']['_entities']
