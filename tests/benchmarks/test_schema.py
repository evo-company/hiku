import pytest

from hiku.extensions.query_parse_cache import QueryParserCache
from hiku.extensions.query_transform_cache import QueryTransformCache
from hiku.extensions.query_validation_cache import QueryValidationCache
from hiku.graph import Graph, Link, Node, Root, Field
from hiku.schema import Schema
from hiku.types import String, TypeRef

from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor

from hiku.federation.engine import Engine as FederatedEngine
from hiku.federation.graph import Graph as FederatedGraph
from hiku.federation.schema import Schema as FedSchema


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


@pytest.fixture(name="schema")
def schema_fixture(graph):
    return Schema(Engine(SyncExecutor()), graph)


@pytest.fixture(name="schema_with_parse_cache")
def schema_with_parse_cache_fixture(graph):
    return Schema(
        Engine(SyncExecutor()),
        graph,
        extensions=[QueryParserCache(2)]
    )


@pytest.fixture(name="schema_with_transform_and_parse_cache")
def schema_with_transform_and_parse_cache_fixture(graph):
    return Schema(
        Engine(SyncExecutor()),
        graph,
        extensions=[
            QueryParserCache(2),
            QueryTransformCache(2),
        ]
    )


@pytest.fixture(name="schema_with_all_caches")
def schema_with_all_caches_fixture(graph):
    return Schema(
        Engine(SyncExecutor()),
        graph,
        extensions=[
            QueryParserCache(2),
            QueryTransformCache(2),
            QueryValidationCache(2),
        ]
    )


@pytest.fixture(name="federated_graph")
def federated_graph_fixture(graph):
    return FederatedGraph(
        graph.nodes + [graph.root]
    )


@pytest.fixture(name="federated_schema")
def federated_schema_fixture(federated_graph):
    return FedSchema(FederatedEngine(SyncExecutor()), federated_graph)


query = """
{ question { text ... on Question { answer } } }
"""

data = {
    "question": {
        "text": "The Ultimate Question of Life, the Universe and Everything",
        "answer": 42
    }
}


def test_federated_schema(benchmark, federated_schema):
    result = benchmark.pedantic(
        federated_schema.execute_sync, args=({"query": query},),
        iterations=5,
        rounds=1000
    )
    assert result == {"data": data}


def test_schema(benchmark, schema):
    result = benchmark.pedantic(
        schema.execute_sync, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}


def test_schema_with_parse_cache(benchmark, schema_with_parse_cache):
    result = benchmark.pedantic(
        schema_with_parse_cache.execute_sync, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}


def test_schema_with_transform_and_parse_cache(benchmark, schema_with_transform_and_parse_cache):
    result = benchmark.pedantic(
        schema_with_transform_and_parse_cache.execute_sync, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}


def test_schema_with_all_caches(benchmark, schema_with_all_caches):
    result = benchmark.pedantic(
        schema_with_all_caches.execute_sync, args=({"query": query},),
        iterations=5,
        rounds=1000
    )

    assert result == {"data": data}
