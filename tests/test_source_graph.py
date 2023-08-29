from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import pytest

from hiku.context import create_execution_context
from hiku.graph import Graph, Node, Link, Field, Option, Root
from hiku.types import Record, Sequence, Any, TypeRef, String
from hiku.engine import Engine
from hiku.builder import build, Q
from hiku.expr.core import define, S, each
from hiku.sources.graph import SubGraph
from hiku.readers.simple import read
from hiku.executors.sync import SyncExecutor
from hiku.executors.threads import ThreadsExecutor

from .base import check_result


DATA = {
    "f1": 7,
    "f2": 8,
    "x": {
        1: {"id": 1, "a": "a1", "b": "b1", "y_id": 6},
        2: {"id": 2, "a": "a2", "b": "b2", "y_id": 5},
        3: {"id": 3, "a": "a3", "b": "b3", "y_id": 4},
    },
    "y": {
        4: {"id": 4, "c": "c1", "d": "d1"},
        5: {"id": 5, "c": "c2", "d": "d2"},
        6: {"id": 6, "c": "c3", "d": "d3"},
    },
    "x1": {
        1: {"with_option": 7},
        2: {"with_option": 8},
        3: {"with_option": 9},
    },
}

_XS_BY_Y_INDEX = defaultdict(list)
for x in DATA["x"].values():
    _XS_BY_Y_INDEX[x["y_id"]].append(x["id"])


def query_f(fields):
    return [DATA[f.name] for f in fields]


def query_x(fields, ids):
    return [[DATA["x"][id_][f.name] for f in fields] for id_ in ids]


def query_y(fields, ids):
    return [[DATA["y"][id_][f.name] for f in fields] for id_ in ids]


def query_x1(fields, ids):
    return [[DATA["x1"][id_][f.name] for f in fields] for id_ in ids]


def to_x():
    return [1, 3, 2]


def to_y():
    return [6, 4, 5]


def x_to_y(ids):
    return [DATA["x"][x_id]["y_id"] for x_id in ids]


def y_to_x(ids):
    return [_XS_BY_Y_INDEX[y_id] for y_id in ids]


_GRAPH = Graph(
    [
        Node(
            "x",
            [
                Field("id", None, query_x),
                Field("a", None, query_x),
                Field("b", None, query_x),
                Field("y_id", None, query_x),
                Link("y", TypeRef["y"], x_to_y, requires="id"),
            ],
        ),
        Node(
            "y",
            [
                Field("id", None, query_y),
                Field("c", None, query_y),
                Field("d", None, query_y),
                Link("xs", Sequence[TypeRef["x"]], y_to_x, requires="id"),
            ],
        ),
        Root(
            [
                Field("f1", None, query_f),
                Field("f2", None, query_f),
            ]
        ),
    ]
)


@define(Record[{"b": Any}], Record[{"d": Any}])
def foo(x, y):
    return "{x[y]} {y[d]}".format(x=x, y=y).upper()


@define(Record[{"b": Any, "y": Record[{"d": Any}]}])
def bar(x):
    return "{x[b]} {x[y][d]}".format(x=x).upper()


@define(Record[{"d": Any, "xs": Sequence[Record[{"b": Any}]]}])
def baz(y):
    xs = ", ".join("{x[b]}".format(x=x) for x in y["xs"])
    return "{y[d]} [{xs}]".format(y=y, xs=xs).upper()


@define(Record[{"a": Any}], Any)
def buz(x, size):
    return "{x[a]} - {size}".format(x=x, size=size)


sg_x = SubGraph(_GRAPH, "x")

sg_y = SubGraph(_GRAPH, "y")


# TODO: refactor
GRAPH = Graph(
    [
        Node(
            "x1",
            [
                Field("id", None, sg_x),
                Field("a", None, sg_x),
                Field("f", None, sg_x.c(S.f1)),
                Field("foo", None, sg_x.c(foo(S.this, S.this.y))),
                Field("bar", None, sg_x.c(bar(S.this))),
                Field("baz", None, sg_x.c(baz(S.this.y))),
                Field(
                    "buz",
                    None,
                    sg_x.c(buz(S.this, S.size)),
                    options=[Option("size", None, default=None)],
                ),
                Field(
                    "buz2",
                    None,
                    sg_x.c(buz(S.this, S.size)),
                    options=[Option("size", None, default=100)],
                ),
                Field(
                    "buz3",
                    None,
                    sg_x.c(buz(S.this, S.size)),
                    options=[Option("size", None)],
                ),
                Field(
                    "with_option", None, query_x1, options=[Option("opt", None)]
                ),
            ],
        ),
        Node(
            "y1",
            [
                Field("id", None, sg_y),
                Field("c", None, sg_y),
                Field("f", None, sg_y.c(S.f2)),
                Field(
                    "foo", None, sg_y.c(each(S.x, S.this.xs, foo(S.x, S.this)))
                ),
                Field("bar", None, sg_y.c(each(S.x, S.this.xs, bar(S.x)))),
                Field("baz", None, sg_y.c(baz(S.this))),
            ],
        ),
        Root(
            [
                Link("x1s", Sequence[TypeRef["x1"]], to_x, requires=None),
                Link("y1s", Sequence[TypeRef["y1"]], to_y, requires=None),
            ]
        ),
    ]
)


@pytest.fixture(name="engine")
def _engine():
    return Engine(ThreadsExecutor(ThreadPoolExecutor(2)))


@pytest.fixture(name="graph")
def _graph():
    return GRAPH


def test_field(engine, graph):
    result = engine.execute(graph, read("[{:x1s [:a :f]}]"))
    check_result(
        result,
        {
            "x1s": [
                {"a": "a1", "f": 7},
                {"a": "a3", "f": 7},
                {"a": "a2", "f": 7},
            ]
        },
    )


def test_field_options(engine, graph):
    result = engine.execute(graph, read('[{:x1s [(:buz {:size "100"})]}]'))
    check_result(
        result,
        {
            "x1s": [
                {"buz": "a1 - 100"},
                {"buz": "a3 - 100"},
                {"buz": "a2 - 100"},
            ]
        },
    )


def test_field_without_options(engine, graph):
    result = engine.execute(graph, read("[{:x1s [:buz]}]"))
    check_result(
        result,
        {
            "x1s": [
                {"buz": "a1 - None"},
                {"buz": "a3 - None"},
                {"buz": "a2 - None"},
            ]
        },
    )


def test_field_without_required_option(engine, graph):
    with pytest.raises(TypeError) as err:
        engine.execute(graph, read("[{:x1s [:buz3]}]"))
    err.match('^Required option "size" for (.*)buz3(.*) was not provided$')


def test_field_option_defaults(engine, graph):
    result = engine.execute(graph, read("[{:x1s [:buz2]}]"))
    check_result(
        result,
        {
            "x1s": [
                {"buz2": "a1 - 100"},
                {"buz2": "a3 - 100"},
                {"buz2": "a2 - 100"},
            ]
        },
    )
    result = engine.execute(graph, read("[{:x1s [(:buz2 {:size 200})]}]"))
    check_result(
        result,
        {
            "x1s": [
                {"buz2": "a1 - 200"},
                {"buz2": "a3 - 200"},
                {"buz2": "a2 - 200"},
            ]
        },
    )


def test_sequence_in_arg_type(engine, graph):
    result = engine.execute(graph, read("[{:x1s [:baz]}]"))
    check_result(
        result,
        {
            "x1s": [
                {"baz": "D3 [B1]"},
                {"baz": "D1 [B3]"},
                {"baz": "D2 [B2]"},
            ]
        },
    )
    result = engine.execute(graph, read("[{:y1s [:baz]}]"))
    check_result(
        result,
        {
            "y1s": [
                {"baz": "D3 [B1]"},
                {"baz": "D1 [B3]"},
                {"baz": "D2 [B2]"},
            ]
        },
    )


def test_mixed_query(engine, graph):
    result = engine.execute(
        graph,
        read("[{:x1s [(:with_option {:opt 123}) :a]}]"),
    )
    check_result(
        result,
        {
            "x1s": [
                {"a": "a1", "with_option": 7},
                {"a": "a3", "with_option": 9},
                {"a": "a2", "with_option": 8},
            ]
        },
    )


def test_complex_field():
    engine = Engine(SyncExecutor())

    def get_a(fields, ids):
        return [[{"s": "bar"} for _ in fields] for _ in ids]

    ll_graph = Graph(
        [
            Node(
                "Foo",
                [
                    Field("a", Record[{"s": String}], get_a),
                ],
            ),
        ]
    )
    foo_sg = SubGraph(ll_graph, "Foo")
    hl_graph = Graph(
        [
            Node(
                "Foo",
                [
                    Field("a", Record[{"s": String}], foo_sg),
                ],
            ),
            Root(
                [
                    Link("foo", TypeRef["Foo"], lambda: 1, requires=None),
                ]
            ),
        ]
    )
    result = engine.execute(hl_graph, build([Q.foo[Q.a[Q.s]]]))
    check_result(result, {"foo": {"a": {"s": "bar"}}})
