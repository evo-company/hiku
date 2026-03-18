import tracemalloc

import pytest

from hiku.graph import Field, Graph, Link, Node, Root
from hiku.types import Integer, Optional, Sequence, String, TypeRef, TypingMeta


def _make_big_graph(n_nodes: int = 100, fields_per_node: int = 20) -> Graph:
    def resolver(fields, ids):
        return [[None] * len(fields) for _ in ids]

    type_variants = [
        String,
        Integer,
        Optional[String],
        Optional[Integer],
        Sequence[String],
        Sequence[Integer],
        Optional[Sequence[String]],
    ]

    nodes = [
        Node(
            f"Node{i}",
            [
                Field(
                    f"field_{j}",
                    type_variants[j % len(type_variants)],
                    resolver,
                )
                for j in range(fields_per_node)
            ],
        )
        for i in range(n_nodes)
    ]
    root = Root(
        [
            Link(f"node{i}", TypeRef[f"Node{i}"], lambda: 1, requires=None)
            for i in range(n_nodes)
        ]
    )
    return Graph(nodes + [root])


def test_type_cache_deduplication():
    assert Optional[String] is Optional[String]
    assert Sequence[Integer] is Sequence[Integer]
    assert Optional[String] is not Optional[Integer]


@pytest.mark.limit_memory("5 MB")
def test_graph_init_memory():
    TypingMeta.__cache__.clear()
    tracemalloc.start()
    try:
        _make_big_graph(100, 20)
        snapshot = tracemalloc.take_snapshot()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        TypingMeta.__cache__.clear()

    stats = snapshot.statistics("lineno")
    print(f"\nPeak: {peak / 1024 / 1024:.2f} MB  (limit 5 MB)")
    print("Top allocators:")
    for stat in stats[:10]:
        print(f"  {stat}")

    limit = 5 * 1024 * 1024  # 5 MB
    assert peak < limit, (
        f"Peak memory {peak / 1024 / 1024:.2f} MB exceeds "
        f"{limit / 1024 / 1024:.0f} MB — type caching may be broken"
    )


def test_sequence_to_type_ref():
    s = Sequence[TypeRef["foo"]]
    assert s.__item_type__ == TypeRef["foo"]


def test_sequence_to_optional_type_ref():
    s = Sequence[Optional[TypeRef["foo"]]]
    assert s.__item_type__ == Optional[TypeRef["foo"]]
