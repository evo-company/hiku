import pytest

from hiku.query import Node, Field, Link
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.v1.endpoint import denormalize_entities
from hiku.federation.v1.engine import Engine
from hiku.federation.v1.validate import validate
from hiku.executors.sync import SyncExecutor

from tests.test_federation_v1.utils import (
    GRAPH,
    ASYNC_GRAPH,
)


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query_, ctx=ctx)


async def execute_async_executor(graph, query_, ctx=None):
    engine = Engine(AsyncIOExecutor())
    return await engine.execute(graph, query_, ctx=ctx)


QUERY = Node(
    fields=[
        Link(
            "_entities",
            Node(
                fields=[
                    Link(
                        "cart",
                        Node(
                            fields=[
                                Field("id"),
                                Field("status"),
                                Link(
                                    "items",
                                    Node(
                                        fields=[
                                            Field("id"),
                                            Field("name"),
                                        ]
                                    ),
                                ),
                            ]
                        ),
                    )
                ]
            ),
            options={
                "representations": [
                    {"__typename": "Order", "cartId": 1},
                    {"__typename": "Order", "cartId": 2},
                ]
            },
        )
    ]
)

SDL_QUERY = Node(fields=[Link("_service", Node(fields=[Field("sdl")]))])


def test_validate_entities_query():
    errors = validate(GRAPH, QUERY)
    assert errors == []


def test_execute_sdl():
    result = execute(GRAPH, SDL_QUERY, {})
    assert result["sdl"] is not None


def test_execute_sync_executor():
    result = execute(GRAPH, QUERY, {})
    data = denormalize_entities(
        GRAPH,
        QUERY,
        result,
    )

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
    assert expect == data
