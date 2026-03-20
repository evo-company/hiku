import gc

import pytest

from hiku.endpoint.graphql import GraphQLEndpoint
from hiku.executors.sync import SyncExecutor
from hiku.extensions.query_parse_cache import QueryParserCache
from hiku.extensions.query_validation_cache import QueryValidationCache
from hiku.graph import Field, Graph, Link, Node, Root
from hiku.schema import Schema
from hiku.types import String, TypeRef


def _make_schema(**kwargs):
    def resolve_question(fields, ids):
        def get_fields(f, id_):
            if f.name == "text":
                return "The Ultimate Question"
            elif f.name == "answer":
                return 42

        return [[get_fields(f, id_) for f in fields] for id_ in ids]

    def link_question():
        return 1

    graph = Graph(
        [
            Node(
                "Question",
                [
                    Field("text", String, resolve_question),
                    Field("answer", String, resolve_question),
                ],
            ),
            Root(
                [
                    Link(
                        "question",
                        TypeRef["Question"],
                        link_question,
                        requires=None,
                    ),
                ]
            ),
        ]
    )
    schema = Schema(SyncExecutor(), graph, **kwargs)
    return GraphQLEndpoint(schema)


query = "{ question { text answer } }"
request = {"query": query}

endpoint = _make_schema()
endpoint_with_caches = _make_schema(
    extensions=[
        QueryParserCache(2),
        QueryValidationCache(2),
    ]
)


def _run_requests(endpoint, n_requests=100):
    # Warm up - let any one-time allocations happen
    for _ in range(10):
        endpoint.dispatch(request)

    gc.collect()

    for _ in range(n_requests):
        result = endpoint.dispatch(request)

    return result


@pytest.mark.limit_memory("50 KB")
def test_endpoint_request_memory():
    result = _run_requests(endpoint, n_requests=100)
    assert result["data"] is not None


@pytest.mark.limit_memory("10 KB")
def test_endpoint_with_caches_request_memory():
    result = _run_requests(endpoint_with_caches, n_requests=100)
    assert result["data"] is not None
