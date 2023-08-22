import pytest

from hiku.extensions import QueryParserCache
from hiku.extensions.query_transform_cache import QueryTransformCache
from hiku.extensions.query_validation_cache import QueryValidationCache
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


@pytest.fixture(name="endpoint_with_parse_cache")
def endpoint_with_parse_cache_fixture(graph):
    return GraphQLEndpoint(Engine(SyncExecutor()), graph, extensions=[
        QueryParserCache(2),
    ])


@pytest.fixture(name="endpoint_with_transform_and_parse_cache")
def endpoint_with_transform_and_parse_cache_fixture(graph):
    return GraphQLEndpoint(Engine(SyncExecutor()), graph, extensions=[
        QueryParserCache(2),
        QueryTransformCache(2),
    ])


@pytest.fixture(name="endpoint_with_all_caches")
def endpoint_with_all_caches_fixture(graph):
    return GraphQLEndpoint(Engine(SyncExecutor()), graph, extensions=[
        QueryParserCache(2),
        QueryTransformCache(2),
        QueryValidationCache(2),
    ])


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


def test_endpoint_with_parse_cache(benchmark, endpoint_with_parse_cache):
    result = benchmark.pedantic(
        endpoint_with_parse_cache.dispatch, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}


def test_endpoint_with_transform_and_parse_cache(benchmark, endpoint_with_transform_and_parse_cache):
    result = benchmark.pedantic(
        endpoint_with_transform_and_parse_cache.dispatch, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}


def test_endpoint_with_all_caches(benchmark, endpoint_with_all_caches):
    result = benchmark.pedantic(
        endpoint_with_all_caches.dispatch, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}
