from __future__ import unicode_literals

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import pytest

from hiku.graph import Graph, Node, Link, Field, Option, Root
from hiku.types import Record, Sequence, Unknown, TypeRef
from hiku.engine import Engine
from hiku.expr.core import define, S, each
from hiku.sources.graph import SubGraph, Expr
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import check_result


DATA = {
    'f1': 7,
    'f2': 8,
    'x': {
        1: {'id': 1, 'a': 'a1', 'b': 'b1', 'y_id': 6},
        2: {'id': 2, 'a': 'a2', 'b': 'b2', 'y_id': 5},
        3: {'id': 3, 'a': 'a3', 'b': 'b3', 'y_id': 4},
    },
    'y': {
        4: {'id': 4, 'c': 'c1', 'd': 'd1'},
        5: {'id': 5, 'c': 'c2', 'd': 'd2'},
        6: {'id': 6, 'c': 'c3', 'd': 'd3'},
    }
}

_XS_BY_Y_INDEX = defaultdict(list)
for x in DATA['x'].values():
    _XS_BY_Y_INDEX[x['y_id']].append(x['id'])


def query_f(fields):
    return [DATA[f.name] for f in fields]


def query_x(fields, ids):
    return [[DATA['x'][id_][f.name] for f in fields] for id_ in ids]


def query_y(fields, ids):
    return [[DATA['y'][id_][f.name] for f in fields] for id_ in ids]


def to_x():
    return [1, 3, 2]


def to_y():
    return [6, 4, 5]


def x_to_y(ids):
    return [DATA['x'][x_id]['y_id'] for x_id in ids]


def y_to_x(ids):
    return [_XS_BY_Y_INDEX[y_id] for y_id in ids]


_GRAPH = Graph([
    Node('x', [
        Field('id', None, query_x),
        Field('a', None, query_x),
        Field('b', None, query_x),
        Field('y_id', None, query_x),
        Link('y', TypeRef['y'], x_to_y, requires='id'),
    ]),
    Node('y', [
        Field('id', None, query_y),
        Field('c', None, query_y),
        Field('d', None, query_y),
        Link('xs', Sequence[TypeRef['x']], y_to_x, requires='id'),
    ]),
    Root([
        Field('f1', None, query_f),
        Field('f2', None, query_f),
    ]),
])


@define(Record[{'b': Unknown}], Record[{'d': Unknown}])
def foo(x, y):
    return '{x[y]} {y[d]}'.format(x=x, y=y).upper()


@define(Record[{'b': Unknown, 'y': Record[{'d': Unknown}]}])
def bar(x):
    return '{x[b]} {x[y][d]}'.format(x=x).upper()


@define(Record[{'d': Unknown, 'xs': Sequence[Record[{'b': Unknown}]]}])
def baz(y):
    xs = ', '.join('{x[b]}'.format(x=x) for x in y['xs'])
    return '{y[d]} [{xs}]'.format(y=y, xs=xs).upper()


@define(Record[{'a': Unknown}], Unknown)
def buz(x, size):
    return '{x[a]} - {size}'.format(x=x, size=size)


sg_x = SubGraph(_GRAPH, 'x')

sg_y = SubGraph(_GRAPH, 'y')


# TODO: refactor
GRAPH = Graph([
    Node('x1', [
        Expr('id', sg_x, S.this.id),
        Expr('a', sg_x, S.this.a),
        Expr('f', sg_x, S.f1),
        Expr('foo', sg_x, foo(S.this, S.this.y)),
        Expr('bar', sg_x, bar(S.this)),
        Expr('baz', sg_x, baz(S.this.y)),
        Expr('buz', sg_x, buz(S.this, S.size),
             options=[Option('size', None, default=None)]),
        Expr('buz2', sg_x, buz(S.this, S.size),
             options=[Option('size', None, default=100)]),
        Expr('buz3', sg_x, buz(S.this, S.size),
             options=[Option('size', None)]),
    ]),
    Node('y1', [
        Expr('id', sg_y, S.this.id),
        Expr('c', sg_y, S.this.c),
        Expr('f', sg_y, S.f2),
        Expr('foo', sg_y, each(S.x, S.this.xs, foo(S.x, S.this))),
        Expr('bar', sg_y, each(S.x, S.this.xs, bar(S.x))),
        Expr('baz', sg_y, baz(S.this)),
    ]),
    Root([
        Link('x1s', Sequence[TypeRef['x1']], to_x, requires=None),
        Link('y1s', Sequence[TypeRef['y1']], to_y, requires=None),
    ]),
])


@pytest.fixture(name='engine')
def _engine():
    return Engine(ThreadsExecutor(ThreadPoolExecutor(2)))


def test_field(engine):
    result = engine.execute(GRAPH, read('[{:x1s [:a :f]}]'))
    check_result(result, {'x1s': [
        {'a': 'a1', 'f': 7},
        {'a': 'a3', 'f': 7},
        {'a': 'a2', 'f': 7},
    ]})


def test_field_options(engine):
    result = engine.execute(GRAPH, read('[{:x1s [(:buz {:size "100"})]}]'))
    check_result(result, {'x1s': [
        {'buz': 'a1 - 100'},
        {'buz': 'a3 - 100'},
        {'buz': 'a2 - 100'},
    ]})


def test_field_without_options(engine):
    result = engine.execute(GRAPH, read('[{:x1s [:buz]}]'))
    check_result(result, {'x1s': [
        {'buz': 'a1 - None'},
        {'buz': 'a3 - None'},
        {'buz': 'a2 - None'},
    ]})


def test_field_without_required_option(engine):
    with pytest.raises(TypeError) as err:
        engine.execute(GRAPH, read('[{:x1s [:buz3]}]'))
    err.match('^Required option "size" for (.*)buz3(.*) was not provided$')


def test_field_option_defaults(engine):
    result = engine.execute(GRAPH, read('[{:x1s [:buz2]}]'))
    check_result(result, {'x1s': [
        {'buz2': 'a1 - 100'},
        {'buz2': 'a3 - 100'},
        {'buz2': 'a2 - 100'},
    ]})
    result = engine.execute(GRAPH, read('[{:x1s [(:buz2 {:size 200})]}]'))
    check_result(result, {'x1s': [
        {'buz2': 'a1 - 200'},
        {'buz2': 'a3 - 200'},
        {'buz2': 'a2 - 200'},
    ]})


def test_sequence_in_arg_type(engine):
    result = engine.execute(GRAPH, read('[{:x1s [:baz]}]'))
    check_result(result, {'x1s': [
        {'baz': 'D3 [B1]'},
        {'baz': 'D1 [B3]'},
        {'baz': 'D2 [B2]'},
    ]})
    result = engine.execute(GRAPH, read('[{:y1s [:baz]}]'))
    check_result(result, {'y1s': [
        {'baz': 'D3 [B1]'},
        {'baz': 'D1 [B3]'},
        {'baz': 'D2 [B2]'},
    ]})
