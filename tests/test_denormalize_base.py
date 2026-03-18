import pytest

from hiku.types import TypeRef, Integer, Sequence, Optional
from hiku.graph import Graph, Node, Field, Root, Link
from hiku.result import ROOT, Proxy, Index, Reference
from hiku.builder import build, Q
from hiku.denormalize.base import Denormalize


def _(*args):
    raise NotImplementedError("Data loading not implemented")


def test_link_record():
    graph = Graph(
        [
            Node(
                "Bar",
                [
                    Field("baz", Integer, _),
                ],
            ),
            Node(
                "Foo",
                [
                    Link("bar", TypeRef["Bar"], _, requires=None),
                ],
            ),
            Root(
                [
                    Link("foo", TypeRef["Foo"], _, requires=None),
                ]
            ),
        ]
    )
    query = build(
        [
            Q.foo[Q.bar[Q.baz,],],
        ]
    )
    index = Index()
    index[ROOT.node][ROOT.ident].update(
        {
            "foo": Reference("Foo", 1),
        }
    )
    index["Foo"][1].update(
        {
            "bar": Reference("Bar", 2),
        }
    )
    index["Bar"][2].update({"baz": 42})
    result = Proxy(index, ROOT, query)
    assert Denormalize(graph, result).process(query) == {
        "foo": {"bar": {"baz": 42}},
    }


def test_link_sequence():
    graph = Graph(
        [
            Node(
                "Bar",
                [
                    Field("baz", Integer, _),
                ],
            ),
            Node(
                "Foo",
                [
                    Link("bar", Sequence[TypeRef["Bar"]], _, requires=None),
                ],
            ),
            Root(
                [
                    Link("foo", Sequence[TypeRef["Foo"]], _, requires=None),
                ]
            ),
        ]
    )
    query = build(
        [
            Q.foo[Q.bar[Q.baz,],],
        ]
    )
    index = Index()
    index[ROOT.node][ROOT.ident].update(
        {
            "foo": [Reference("Foo", 1)],
        }
    )
    index["Foo"][1].update(
        {
            "bar": [Reference("Bar", 2), Reference("Bar", 3)],
        }
    )
    index["Bar"][2].update({"baz": 42})
    index["Bar"][3].update({"baz": 43})
    result = Proxy(index, ROOT, query)
    assert Denormalize(graph, result).process(query) == {
        "foo": [
            {
                "bar": [
                    {"baz": 42},
                    {"baz": 43},
                ],
            },
        ],
    }


@pytest.mark.parametrize(
    "value, expected", [(None, None), (Reference("Bar", 2), {"baz": 42})]
)
def test_link_optional(value, expected):
    graph = Graph(
        [
            Node(
                "Bar",
                [
                    Field("baz", Integer, _),
                ],
            ),
            Node(
                "Foo",
                [
                    Link("bar", Optional[TypeRef["Bar"]], _, requires=None),
                ],
            ),
            Root(
                [
                    Link("foo", Optional[TypeRef["Foo"]], _, requires=None),
                ]
            ),
        ]
    )
    query = build(
        [
            Q.foo[Q.bar[Q.baz,],],
        ]
    )
    index = Index()
    index[ROOT.node][ROOT.ident].update(
        {
            "foo": Reference("Foo", 1),
        }
    )
    index["Foo"][1].update(
        {
            "bar": value,
        }
    )
    index["Bar"][2].update({"baz": 42})
    result = Proxy(index, ROOT, query)
    assert Denormalize(graph, result).process(query) == {
        "foo": {
            "bar": expected,
        },
    }
