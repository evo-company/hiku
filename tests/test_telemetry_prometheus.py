import faker
import pytest

from prometheus_client import REGISTRY

from hiku import query as q
from hiku.executors.sync import SyncExecutor
from hiku.graph import Graph, Node, Field, Link, Root, apply
from hiku.schema import Schema
from hiku.types import TypeRef
from hiku.engine import pass_context
from hiku.sources.graph import SubGraph
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.telemetry.prometheus import GraphMetrics, AsyncGraphMetrics

from tests.base import check_result


fake = faker.Faker()


@pytest.fixture(name="graph_name")
def graph_name_fixture():
    return fake.pystr()


@pytest.fixture(name="sample_count")
def sample_count_fixture(graph_name):
    def sample_count(node, field):
        return REGISTRY.get_sample_value(
            "graph_field_time_count",
            dict(graph=graph_name, node=node, field=field),
        )

    return sample_count


def test_simple_sync(graph_name, sample_count):
    def x_fields(fields, ids):
        return [[42 for _ in fields] for _ in ids]

    def root_fields(fields):
        return [1 for _ in fields]

    def x_link():
        return 2

    ll_graph = Graph(
        [
            Node(
                "X",
                [
                    Field("id", None, x_fields),
                ],
            ),
        ]
    )

    x_sg = SubGraph(ll_graph, "X")

    hl_graph = Graph(
        [
            Node(
                "X",
                [
                    Field("id", None, x_sg),
                ],
            ),
            Root(
                [
                    Field("a", None, root_fields),
                    Link("x", TypeRef["X"], x_link, requires=None),
                ]
            ),
        ]
    )

    hl_graph = apply(hl_graph, [GraphMetrics(graph_name)])

    assert sample_count("Root", "a") is None
    assert sample_count("Root", "x") is None
    assert sample_count("X", "id") is None

    query = q.Node(
        [
            q.Field("a"),
            q.Link(
                "x",
                q.Node(
                    [
                        q.Field("id"),
                    ]
                ),
            ),
        ]
    )

    schema = Schema(SyncExecutor(), hl_graph)
    result = schema.execute_sync(query)
    check_result(
        result.data,
        {
            "a": 1,
            "x": {
                "id": 42,
            },
        },
    )

    assert sample_count("Root", "a") == 1.0
    assert sample_count("Root", "x") == 1.0
    assert sample_count("X", "id") == 1.0


@pytest.mark.asyncio
async def test_simple_async(graph_name, sample_count):
    async def x_fields(fields, ids):
        return [[42 for _ in fields] for _ in ids]

    async def root_fields(fields):
        return [1 for _ in fields]

    async def x_link():
        return 2

    ll_graph = Graph(
        [
            Node(
                "X",
                [
                    Field("id", None, x_fields),
                ],
            ),
        ]
    )

    x_sg = SubGraph(ll_graph, "X")

    hl_graph = Graph(
        [
            Node(
                "X",
                [
                    Field("id", None, x_sg),
                ],
            ),
            Root(
                [
                    Field("a", None, root_fields),
                    Link("x", TypeRef["X"], x_link, requires=None),
                ]
            ),
        ]
    )

    hl_graph = apply(hl_graph, [AsyncGraphMetrics(graph_name)])

    query = q.Node(
        [
            q.Field("a"),
            q.Link(
                "x",
                q.Node(
                    [
                        q.Field("id"),
                    ]
                ),
            ),
        ]
    )

    assert sample_count("Root", "a") is None
    assert sample_count("Root", "x") is None
    assert sample_count("X", "id") is None

    schema = Schema(AsyncIOExecutor(), hl_graph)
    result = await schema.execute(query)

    check_result(
        result.data,
        {
            "a": 1,
            "x": {
                "id": 42,
            },
        },
    )

    assert sample_count("Root", "a") == 1.0
    assert sample_count("Root", "x") == 1.0
    assert sample_count("X", "id") == 1.0


def test_with_pass_context(graph_name, sample_count):
    def root_fields1(fields):
        return [1 for _ in fields]

    @pass_context
    def root_fields2(ctx, fields):
        return [2 for _ in fields]

    graph = Graph(
        [
            Root(
                [
                    Field("a", None, root_fields1),
                    Field("b", None, root_fields2),
                ]
            ),
        ]
    )

    graph = apply(graph, [GraphMetrics(graph_name)])

    assert sample_count("Root", "a") is None
    assert sample_count("Root", "b") is None

    query = q.Node(
        [
            q.Field("a"),
            q.Field("b"),
        ]
    )

    schema = Schema(SyncExecutor(), graph)
    result = schema.execute_sync(query)

    check_result(
        result.data,
        {
            "a": 1,
            "b": 2,
        },
    )

    assert sample_count("Root", "a") == 1.0
    assert sample_count("Root", "b") == 1.0
