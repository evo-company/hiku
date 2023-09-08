from typing import Dict

import pytest
from hiku.graph import Graph

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.endpoint import (
    FederatedGraphQLEndpoint,
    AsyncFederatedGraphQLEndpoint,
)
from hiku.federation.engine import Engine
from hiku.executors.sync import SyncExecutor

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH
)


def execute_v1(query: Dict, graph: Graph):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
        federation_version=1
    )

    return graphql_endpoint.dispatch(query)


async def execute_async_v1(query: Dict, graph: Graph):
    graphql_endpoint = AsyncFederatedGraphQLEndpoint(
        Engine(AsyncIOExecutor()),
        graph,
        federation_version=1
    )

    return await graphql_endpoint.dispatch(query)


def execute_v2(query: Dict, graph: Graph):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query)


async def execute_async_v2(query: Dict, graph: Graph):
    graphql_endpoint = AsyncFederatedGraphQLEndpoint(
        Engine(AsyncIOExecutor()),
        graph,
    )

    return await graphql_endpoint.dispatch(query)


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

SDL_QUERY = {'query': '{_service {sdl}}'}

Q = {
    'query': """
    query __ApolloGetServiceDefinition__ { _service { sdl } }
    """,
    'variables': None,
    'operationName': '__ApolloGetServiceDefinition__',
}


@pytest.mark.parametrize('executor', [
    execute_v1,
    execute_v2,
])
def test_fetch_sdl(executor):
    result = executor(Q, GRAPH)
    assert result['data']['_service']['sdl'] is not None


@pytest.mark.parametrize('executor', [
    execute_async_v1,
    execute_async_v2,
])
@pytest.mark.asyncio
async def test_fetch_sdl_async(executor):
    result = await executor(Q, ASYNC_GRAPH)
    assert result['data']['_service']['sdl'] is not None


@pytest.mark.parametrize('executor', [
    execute_v1,
    execute_v2,
])
def test_execute_sync_executor(executor):
    result = executor(ENTITIES_QUERY, GRAPH)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result['data']['_entities']


@pytest.mark.asyncio
@pytest.mark.parametrize('executor', [
    execute_async_v1,
    execute_async_v2,
])
async def test_execute_async_executor(executor):
    result = await executor(ENTITIES_QUERY, ASYNC_GRAPH)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result['data']['_entities']
