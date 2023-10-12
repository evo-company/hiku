import pytest

from hiku.endpoint.graphql import GraphQLEndpoint
from hiku.engine import Engine, pass_context
from hiku.executors.sync import SyncExecutor
from hiku.extensions.context import CustomContext
from hiku.graph import Field, Graph, Root
from hiku.types import String


@pytest.fixture(name="sync_graph")
def sync_graph_fixture():
    def question(fields):
        return ["Number?" for _ in fields]

    @pass_context
    def answer(ctx, fields):
        return [ctx["answer"] for _ in fields]

    return Graph(
        [
            Root(
                [
                    Field("question", String, question),
                    Field("answer", String, answer),
                ]
            )
        ]
    )


def test_custom_context_extension(sync_graph):
    endpoint = GraphQLEndpoint(
        Engine(SyncExecutor()),
        sync_graph,
        extensions=[CustomContext(lambda _: {"answer": "42"})],
    )

    result = endpoint.dispatch({"query": "{answer}"}, {"a": "b"})
    assert result == {"data": {"answer": "42"}}
