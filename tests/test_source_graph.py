from __future__ import unicode_literals

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from hiku.expr import define, S, each
from hiku.graph import Graph, Edge, Link, Field, Option, Root, MANY, ONE
from hiku.engine import Engine
from hiku.sources.graph import SubGraph, Expr
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import TestCase


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
    return [1, 2, 3]


def to_y():
    return [6, 5, 4]


def x_to_y(ids):
    return [DATA['x'][x_id]['y_id'] for x_id in ids]


def y_to_x(ids):
    return [_XS_BY_Y_INDEX[y_id] for y_id in ids]


_GRAPH = Graph([
    Edge('x', [
        Field('id', query_x),
        Field('a', query_x),
        Field('b', query_x),
        Field('y_id', query_x),
        Link('y', ONE, x_to_y, edge='y', requires='id'),
    ]),
    Edge('y', [
        Field('id', query_y),
        Field('c', query_y),
        Field('d', query_y),
        Link('xs', MANY, y_to_x, edge='x', requires='id'),
    ]),
    Root([
        Field('f1', query_f),
        Field('f2', query_f),
        Link('xs', MANY, to_x, edge='x', requires=None),
        Link('ys', MANY, to_y, edge='y', requires=None),
    ]),
])


@define('[[:b] [:d]]')
def foo(x, y):
    return '{x[y]} {y[d]}'.format(x=x, y=y).upper()


@define('[[:b {:y [:d]}]]')
def bar(x):
    return '{x[b]} {x[y][d]}'.format(x=x).upper()


@define('[[:d {:xs [:b]}]]')
def baz(y):
    xs = ', '.join('{x[b]}'.format(x=x) for x in y['xs'])
    return '{y[d]} [{xs}]'.format(y=y, xs=xs).upper()


@define('[[:a] nil]')
def buz(x, size):
    return '{x[a]} - {size}'.format(x=x, size=size)


sg_x = SubGraph(_GRAPH, 'x')

sg_y = SubGraph(_GRAPH, 'y')


# TODO: refactor
GRAPH = Graph([
    Edge('x1', [
        Expr('id', sg_x, S.this.id),
        Expr('a', sg_x, S.this.a),
        Expr('f', sg_x, S.f1),
        Expr('foo', sg_x, foo(S.this, S.this.y)),
        Expr('bar', sg_x, bar(S.this)),
        # Expr('baz', baz(S.this.y)),
        Expr('buz', sg_x, buz(S.this, S.size), options=[Option('size')]),
        Expr('buz2', sg_x, buz(S.this, S.size),
             options=[Option('size', default=100)]),
    ]),
    Edge('y1', [
        Expr('id', sg_y, S.this.id),
        Expr('c', sg_y, S.this.c),
        Expr('f', sg_y, S.f2),
        Expr('foo', sg_y, each(S.x, S.this.xs, foo(S.x, S.this))),
        Expr('bar', sg_y, each(S.x, S.this.xs, bar(S.x))),
        # Expr('baz', baz(S.this)),
    ]),
    Root([
        Edge('x1', [
            Expr('id', sg_x, S.this.id),
            Expr('a', sg_x, S.this.a),
            Expr('f', sg_x, S.f1),
            Expr('foo', sg_x, foo(S.this, S.this.y)),
            Expr('bar', sg_x, bar(S.this)),
            # Expr('baz', baz(S.this.y)),
            Expr('buz', sg_x, buz(S.this, S.size), options=[Option('size')]),
            Expr('buz2', sg_x, buz(S.this, S.size),
                 options=[Option('size', default=100)]),
        ]),
        Edge('y1', [
            Expr('id', sg_y, S.this.id),
            Expr('c', sg_y, S.this.c),
            Expr('f', sg_y, S.f2),
            Expr('foo', sg_y, each(S.x, S.this.xs, foo(S.x, S.this))),
            Expr('bar', sg_y, each(S.x, S.this.xs, bar(S.x))),
            # Expr('baz', baz(S.this)),
        ]),
        # TODO: links reuse
        Link('x1s', MANY, to_x, edge='x1', requires=None),
        Link('y1s', MANY, to_y, edge='y2', requires=None),
    ]),
])


class TestSourceGraph(TestCase):

    def setUp(self):
        self.engine = Engine(ThreadsExecutor(ThreadPoolExecutor(2)))

    def testField(self):
        result = self.engine.execute(GRAPH, read('[{:x1s [:a :f]}]'))
        self.assertResult(result, {'x1s': [
            {'a': 'a1', 'f': 7},
            {'a': 'a2', 'f': 7},
            {'a': 'a3', 'f': 7},
        ]})

    def testFieldOptions(self):
        result = self.engine.execute(GRAPH,
                                     read('[{:x1s [(:buz {:size "100"})]}]'))
        self.assertResult(result, {'x1s': [
            {'buz': 'a1 - 100'},
            {'buz': 'a2 - 100'},
            {'buz': 'a3 - 100'},
        ]})

    def testFieldWithoutOptions(self):
        result = self.engine.execute(GRAPH,
                                     read('[{:x1s [:buz]}]'))
        self.assertResult(result, {'x1s': [
            {'buz': 'a1 - None'},
            {'buz': 'a2 - None'},
            {'buz': 'a3 - None'},
        ]})

    def testFieldOptionDefaults(self):
        result = self.engine.execute(GRAPH,
                                     read('[{:x1s [:buz2]}]'))
        self.assertResult(result, {'x1s': [
            {'buz2': 'a1 - 100'},
            {'buz2': 'a2 - 100'},
            {'buz2': 'a3 - 100'},
        ]})
        result = self.engine.execute(GRAPH,
                                     read('[{:x1s [(:buz2 {:size 200})]}]'))
        self.assertResult(result, {'x1s': [
            {'buz2': 'a1 - 200'},
            {'buz2': 'a2 - 200'},
            {'buz2': 'a3 - 200'},
        ]})
