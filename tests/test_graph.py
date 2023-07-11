from hiku.graph import Field, Graph, Link, Node, Root
from hiku.types import Optional, Sequence, String, TypeRef


def noop(*args, **kwargs):
    pass


def test_link_with_sequence_to_type_ref():
    graph = Graph([
        Node('A', [
            Field('a', String, noop)
        ]),
        Root([
            Link('a', Sequence[TypeRef['A']], noop, requires=None)
        ])
    ])

    assert len(graph.nodes) == 1


def test_link_with_sequence_to_optional_type_ref():
    graph = Graph([
        Node('A', [
            Field('a', String, noop)
        ]),
        Root([
            Link('a', Sequence[Optional[TypeRef['A']]], noop, requires=None)
        ])
    ])

    assert len(graph.nodes) == 1
