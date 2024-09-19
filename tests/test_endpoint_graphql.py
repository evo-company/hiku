import pytest

from hiku.endpoint.graphql import (
    AsyncGraphQLEndpoint,
    BatchGraphQLEndpoint,
    GraphQLEndpoint,
)
from hiku.engine import pass_context
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.executors.sync import SyncExecutor
from hiku.extensions.context import CustomContext
from hiku.graph import Field, Graph, Root
from hiku.schema import Schema
from hiku.types import String


@pytest.fixture(name="sync_graph")
def sync_graph_fixture():
    def answer(fields):
        return ["42" for _ in fields]

    return Graph([Root([Field("answer", String, answer)])])


@pytest.fixture(name="async_graph")
def async_graph_fixture():
    @pass_context
    async def answer(ctx, fields):
        return [ctx.get("default_answer") or "42" for _ in fields]

    return Graph([Root([Field("answer", String, answer)])])


def test_endpoint(sync_graph):
    endpoint = GraphQLEndpoint(Schema(SyncExecutor(), sync_graph))
    result = endpoint.dispatch({"query": "{answer}"})
    assert result == {"data": {"answer": "42"}}


def test_batch_endpoint(sync_graph):
    endpoint = BatchGraphQLEndpoint(Schema(SyncExecutor(), sync_graph))

    assert endpoint.dispatch([]) == []

    result = endpoint.dispatch({"query": "{answer}"})
    assert result == {"data": {"answer": "42"}}

    batch_result = endpoint.dispatch(
        [
            {"query": "{answer}"},
            {"query": "{__typename}"},
        ]
    )
    assert batch_result == [
        {"data": {"answer": "42"}},
        {"data": {"__typename": "Query"}},
    ]


@pytest.mark.asyncio
async def test_async_endpoint(async_graph):
    endpoint = AsyncGraphQLEndpoint(Schema(AsyncIOExecutor(), async_graph))
    result = await endpoint.dispatch(
        {"query": "{answer}"}, context={"default_answer": "52"}
    )
    assert result == {"data": {"answer": "52"}}


@pytest.mark.asyncio
async def test_async_batch_endpoint(async_graph):
    endpoint = AsyncGraphQLEndpoint(
        Schema(
            AsyncIOExecutor(),
            async_graph,
        ),
        batching=True,
    )

    assert await endpoint.dispatch([]) == []

    result = await endpoint.dispatch({"query": "{answer}"})
    assert result == {"data": {"answer": "42"}}

    batch_result = await endpoint.dispatch(
        [
            {"query": "{answer}"},
            {"query": "{__typename}"},
        ],
        context={"default_answer": "52"},
    )
    assert batch_result == [
        {"data": {"answer": "52"}},
        {"data": {"__typename": "Query"}},
    ]


@pytest.mark.asyncio
async def test_async_batch_endpoint_with_custom_context(async_graph):
    def get_custom_context(ec):
        return {"default_answer": "52"}

    endpoint = AsyncGraphQLEndpoint(
        Schema(
            AsyncIOExecutor(),
            async_graph,
            extensions=[CustomContext(get_custom_context)],
        ),
        batching=True,
    )

    assert await endpoint.dispatch([]) == []

    result = await endpoint.dispatch({"query": "{answer}"})
    assert result == {"data": {"answer": "52"}}

    batch_result = await endpoint.dispatch(
        [
            {"query": "{answer}"},
            {"query": "{__typename}"},
        ]
    )
    assert batch_result == [
        {"data": {"answer": "52"}},
        {"data": {"__typename": "Query"}},
    ]
