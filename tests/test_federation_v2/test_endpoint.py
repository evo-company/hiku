import pytest

from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.v2.endpoint import (
    FederatedGraphQLEndpoint,
    AsyncFederatedGraphQLEndpoint,
)
from hiku.federation.v2.engine import Engine
from hiku.executors.sync import SyncExecutor

from tests.test_federation_v2.utils import (
    GRAPH,
    ASYNC_GRAPH,
)


def execute(graph, query_dict):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_dict)


async def execute_async(graph, query_dict):
    graphql_endpoint = AsyncFederatedGraphQLEndpoint(
        Engine(AsyncIOExecutor()),
        graph,
    )

    return await graphql_endpoint.dispatch(query_dict)


ENTITIES_QUERY = {
    'query': """
        query($representations:[_Any!]!) {
            _entities(representations:$representations) {
                ...on Order {
                    cart {
                        id
                        status
                    }
                }
            }
        }
        """,
    'variables': {
        'representations': [
            {'__typename': 'Order', 'cartId': 1},
            {'__typename': 'Order', 'cartId': 2},
        ]
    }
}

SDL_QUERY = {'query': '{_service {sdl}}'}


def test_execute_sdl():
    result = execute(GRAPH, SDL_QUERY)
    assert result['data']['_service']['sdl'] is not None


def test_execute_sync_executor():
    result = execute(GRAPH, ENTITIES_QUERY)

    expect = [
        {'cart': {'id': 1, 'status': 'NEW'}},
        {'cart': {'id': 2, 'status': 'ORDERED'}}
    ]
    assert expect == result['data']['_entities']


@pytest.mark.asyncio
async def test_execute_async_executor():
    result = await execute_async(ASYNC_GRAPH, ENTITIES_QUERY)

    expect = [
        {'cart': {'id': 1, 'status': 'NEW'}},
        {'cart': {'id': 2, 'status': 'ORDERED'}}
    ]
    assert expect == result['data']['_entities']
