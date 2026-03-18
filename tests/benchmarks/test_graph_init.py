from hiku.graph import Field, Graph, Link, Node, Root
from hiku.types import Integer, Optional, Sequence, String, TypeRef


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


def test_graph_init_speed(benchmark):
    benchmark.pedantic(_make_big_graph, iterations=3, rounds=100)
