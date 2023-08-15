import pytest

from hiku.graph import Graph, Root, Field
from hiku.types import String

from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.endpoint.graphql import GraphQLEndpoint

from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine as FederatedEngine
from hiku.federation.graph import Graph as FederatedGraph


@pytest.fixture(name="graph")
def graph_fixture():
    def answer(fields):
        return ["42" for _ in fields]

    return Graph([Root([Field("answer", String, answer)])])


@pytest.fixture(name="endpoint")
def endpoint_fixture(graph):
    return GraphQLEndpoint(Engine(SyncExecutor()), graph)


@pytest.fixture(name="federated_graph")
def federated_graph_fixture():
    def answer(fields):
        return ["42" for _ in fields]

    return FederatedGraph([Root([Field("answer", String, answer)])])


@pytest.fixture(name="federated_endpoint")
def federated_endpoint_fixture(federated_graph):
    return FederatedGraphQLEndpoint(
        FederatedEngine(SyncExecutor()),
        federated_graph
    )


def test_federated_endpoint(benchmark, federated_endpoint):
    result = benchmark.pedantic(
        federated_endpoint.dispatch, args=({"query": "{answer}"},),
        iterations=5,
        rounds=1000
    )
    assert result == {"data": {"answer": "42"}}


def test_endpoint(benchmark, endpoint):
    result = benchmark.pedantic(
        endpoint.dispatch, args=({"query": "{answer}"},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": {"answer": "42"}}