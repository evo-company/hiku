import pytest

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.endpoint import (
    FederatedGraphQLEndpoint,
    AsyncFederatedGraphQLEndpoint,
)
from hiku.federation.engine import Engine
from hiku.executors.sync import SyncExecutor

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH,
)


def execute_v1(graph, query_dict):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor(), federation_version=1),
        graph,
    )

    return graphql_endpoint.dispatch(query_dict)


async def execute_async_v1(graph, query_dict):
    graphql_endpoint = AsyncFederatedGraphQLEndpoint(
        Engine(AsyncIOExecutor(), federation_version=1),
        graph,
    )

    return await graphql_endpoint.dispatch(query_dict)


def execute_v2(graph, query_dict):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_dict)


async def execute_async_v2(graph, query_dict):
    graphql_endpoint = AsyncFederatedGraphQLEndpoint(
        Engine(AsyncIOExecutor()),
        graph,
    )

    return await graphql_endpoint.dispatch(query_dict)


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


@pytest.mark.parametrize('executor', [
    execute_v1,
    execute_v2,
])
def test_fetch_sdl(executor):
    result = executor(GRAPH, SDL_QUERY)
    assert result['data']['_service']['sdl'] is not None


@pytest.mark.parametrize('executor', [
    execute_v1,
    execute_v2,
])
def test_execute_sync_executor(executor):
    result = executor(GRAPH, ENTITIES_QUERY)

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
    result = await executor(ASYNC_GRAPH, ENTITIES_QUERY)

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == result['data']['_entities']
