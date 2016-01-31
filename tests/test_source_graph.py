from __future__ import unicode_literals

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from hiku.dsl import define, S, each
from hiku.graph import Edge, Link, Field
from hiku.engine import Engine
from hiku.sources.graph import subquery_fields
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import TestCase


DATA = {
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


def query_x(fields, ids):
    return [[DATA['x'][id_][f] for f in fields] for id_ in ids]


def query_y(fields, ids):
    return [[DATA['y'][id_][f] for f in fields] for id_ in ids]


def to_x():
    return [1, 2, 3]


def to_y():
    return [6, 5, 4]


def x_to_y(ids):
    return [DATA['x'][x_id]['y_id'] for x_id in ids]


def y_to_x(ids):
    return [_XS_BY_Y_INDEX[y_id] for y_id in ids]


LOW_ENV = Edge(None, [
    Edge('x', [
        Field('id', query_x),
        Field('a', query_x),
        Field('b', query_x),
        Field('y_id', query_x),
        Link('y', 'id', 'y', x_to_y, to_list=False),
    ]),
    Edge('y', [
        Field('id', query_y),
        Field('c', query_y),
        Field('d', query_y),
        Link('xs', 'id', 'x', y_to_x, to_list=True),
    ]),
    Link('xs', None, 'x', to_x, to_list=True),
    Link('ys', None, 'y', to_y, to_list=True),
])


@define('[[:b] [:d]]', _name='foo')
def foo(x, y):
    return '{x[y]} {y[d]}'.format(x=x, y=y).upper()


@define('[[:b {:y [:d]}]]', _name='bar')
def bar(x):
    return '{x[b]} {x[y][d]}'.format(x=x).upper()


@define('[[:d {:xs [:b]}]]', _name='baz')
def baz(y):
    xs = ', '.join('{x[b]}'.format(x=x) for x in y['xs'])
    return '{y[d]} [{xs}]'.format(y=y, xs=xs).upper()


HIGH_ENV = Edge(None, [
    Edge('x1', subquery_fields(LOW_ENV, 'x', {
        'id': S.this.id,
        'a': S.this.a,
        'foo': foo(S.this, S.this.y),
        'bar': bar(S.this),
        'baz': baz(S.this.y),
        # 'y': S.this.y,
    })),
    Edge('y1', subquery_fields(LOW_ENV, 'y', {
        'id': S.this.id,
        'c': S.this.c,
        'foo': each(S.x, S.this.xs, foo(S.x, S.this)),
        'bar': each(S.x, S.this.xs, bar(S.x)),
        'baz': baz(S.this),
        # 'xs': S.this.xs,
    })),
    # TODO: links reuse
    Link('xs1', None, 'x1', to_x, to_list=True),
    Link('ys2', None, 'y2', to_y, to_list=True),
])


class TestSourceGraph(TestCase):

    def setUp(self):
        self.engine = Engine(ThreadsExecutor(ThreadPoolExecutor(2)))

    def testField(self):
        result = self.engine.execute(HIGH_ENV, read('[{:xs1 [:a]}]'))
        self.assertResult(result, {'xs1': [
            {'a': 'a1'},
            {'a': 'a2'},
            {'a': 'a3'},
        ]})
