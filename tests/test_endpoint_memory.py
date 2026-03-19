import tracemalloc

import pytest

from hiku.endpoint.graphql import GraphQLEndpoint
from hiku.executors.sync import SyncExecutor
from hiku.extensions.query_parse_cache import QueryParserCache
from hiku.extensions.query_validation_cache import QueryValidationCache
from hiku.graph import Graph, Link, Node, Root, Field
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


def _measure_request_memory(endpoint, n_requests=100):
    # Warm up - let any one-time allocations happen
    for _ in range(10):
        endpoint.dispatch(request)

    tracemalloc.start()
    try:
        snapshot_before = tracemalloc.take_snapshot()
        mem_before = tracemalloc.get_traced_memory()[0]

        for _ in range(n_requests):
            endpoint.dispatch(request)

        snapshot_after = tracemalloc.take_snapshot()
        mem_after = tracemalloc.get_traced_memory()[0]
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    diff = snapshot_after.compare_to(snapshot_before, "lineno")
    allocated = mem_after - mem_before

    print(f"\nAfter {n_requests} requests:")
    print(f"  Current memory delta: {allocated / 1024:.1f} KB")
    print(f"  Peak memory: {peak / 1024:.1f} KB")
    print(f"  Per-request: {allocated / n_requests / 1024:.2f} KB")
    print("  Top allocations (delta):")
    for stat in diff[:10]:
        print(f"    {stat}")

    return allocated, peak


@pytest.mark.limit_memory("200 KB")
def test_endpoint_request_memory():
    endpoint = _make_schema()
    allocated, peak = _measure_request_memory(endpoint, n_requests=100)

    per_request = allocated / 100
    limit = 10 * 1024  # 10 KB per request
    assert per_request < limit, (
        f"Per-request memory {per_request / 1024:.2f} KB exceeds "
        f"{limit / 1024:.0f} KB limit — possible memory leak"
    )


@pytest.mark.limit_memory("300 KB")
def test_endpoint_with_caches_request_memory():
    endpoint = _make_schema(
        extensions=[
            QueryParserCache(2),
            QueryValidationCache(2),
        ]
    )
    allocated, peak = _measure_request_memory(endpoint, n_requests=100)

    per_request = allocated / 100
    limit = 10 * 1024  # 10 KB per request
    assert per_request < limit, (
        f"Per-request memory {per_request / 1024:.2f} KB exceeds "
        f"{limit / 1024:.0f} KB limit — possible memory leak"
    )
