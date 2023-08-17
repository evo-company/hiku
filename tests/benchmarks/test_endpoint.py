import pytest

from hiku.graph import Graph, Link, Node, Root, Field
from hiku.types import String, TypeRef

from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.endpoint.graphql import GraphQLEndpoint

from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine as FederatedEngine
from hiku.federation.graph import Graph as FederatedGraph


@pytest.fixture(name="graph")
def graph_fixture():
    def resolve_question(fields, ids):
        def get_fields(f, id_):
            if f.name == 'text':
                return 'The Ultimate Question of Life, the Universe and Everything'
            elif f.name == 'answer':
                return 42

        return [
            [get_fields(f, id_) for f in fields]
            for id_ in ids
        ]

    def link_question():
        return 1

    return Graph([
        Node('Question', [
            Field('text', String, resolve_question),
            Field('answer', String, resolve_question),
        ]),
        Root([
            Link('question', TypeRef['Question'], link_question, requires=None),
        ])])


@pytest.fixture(name="endpoint")
def endpoint_fixture(graph):
    return GraphQLEndpoint(Engine(SyncExecutor()), graph)


@pytest.fixture(name="federated_graph")
def federated_graph_fixture(graph):
    return FederatedGraph(
        graph.nodes + [graph.root],
    )


@pytest.fixture(name="federated_endpoint")
def federated_endpoint_fixture(federated_graph):
    return FederatedGraphQLEndpoint(
        FederatedEngine(SyncExecutor()),
        federated_graph
    )


query = """
{ question { text ... on Question { answer } } }
"""

data = {
    "question": {
        "text": "The Ultimate Question of Life, the Universe and Everything",
        "answer": 42
    }
}


def test_federated_endpoint(benchmark, federated_endpoint):
    result = benchmark.pedantic(
        federated_endpoint.dispatch, args=({"query": query},),
        iterations=5,
        rounds=1000
    )
    assert result == {"data": data}


def test_endpoint(benchmark, endpoint):
    result = benchmark.pedantic(
        endpoint.dispatch, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}
