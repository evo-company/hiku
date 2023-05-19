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
    "query": """
        query($representations:[_Any!]!) {
            _entities(representations:$representations) {
                ...on Order {
                    cart {
                        id
                        status
                        items { id name }
                    }
                }
            }
        }
        """,
    "variables": {
        "representations": [
            {"__typename": "Order", "cartId": 1},
            {"__typename": "Order", "cartId": 2},
        ]
    },
}

SDL_QUERY = {"query": "{_service {sdl}}"}


def test_execute_sdl():
    result = execute(GRAPH, SDL_QUERY)
    assert result["data"]["_service"]["sdl"] is not None


def test_execute_sync_executor():
    result = execute(GRAPH, ENTITIES_QUERY)

    expect = [
        {
            "cart": {
                "id": 1,
                "status": "NEW",
                "items": [{"id": 10, "name": "Ipad"}],
            }
        },
        {
            "cart": {
                "id": 2,
                "status": "ORDERED",
                "items": [
                    {"id": 20, "name": "Book"},
                    {"id": 21, "name": "Pen"},
                ],
            }
        },
    ]
    assert expect == result["data"]["_entities"]


@pytest.mark.asyncio
async def test_execute_async_executor():
    result = await execute_async(ASYNC_GRAPH, ENTITIES_QUERY)

    expect = [
        {
            "cart": {
                "id": 1,
                "status": "NEW",
                "items": [{"id": 10, "name": "Ipad"}],
            }
        },
        {
            "cart": {
                "id": 2,
                "status": "ORDERED",
                "items": [
                    {"id": 20, "name": "Book"},
                    {"id": 21, "name": "Pen"},
                ],
            }
        },
    ]
    assert expect == result["data"]["_entities"]
