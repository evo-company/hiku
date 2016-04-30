from hiku import graph
from hiku.expr import define, S, to_expr
from hiku.refs import NamedRef
from hiku.checker import check, graph_types, fn_types

from .base import TestCase, ref_eq_patcher


@define('[[:a :c] [:d :f]]')
def foo(x, y):
    pass


@define('[[:e {:x1 [:b]}]]')
def bar(y):
    pass


@define('[[:e {:xs [:b]}]]')
def baz(y):
    pass


@define('[[:a :c] nil [:d :f] nil]')
def buz(x, m, y, n):
    pass


def noop(*_):
    return 1/0


ENV = graph.Graph([
    graph.Field('f', noop),
    graph.Edge('x', [
        graph.Field('a', noop),
        graph.Field('b', noop),
        graph.Field('c', noop),
    ]),
    graph.Link('x1', noop, edge='x', requires=None, to_list=False),
    graph.Link('xs', noop, edge='x', requires=None, to_list=True),
    graph.Edge('y', [
        graph.Field('d', noop),
        graph.Field('e', noop),
        graph.Field('f', noop),
        graph.Link('x1', noop, edge='x', requires=None, to_list=False),
        graph.Link('xs', noop, edge='x', requires=None, to_list=True),
    ]),
    graph.Link('y1', noop, edge='y', requires=None, to_list=False),
    graph.Link('ys', noop, edge='y', requires=None, to_list=True),
])

TYPES = graph_types(ENV)


class TestChecker(TestCase):

    def check(self, expr):
        expr, functions = to_expr(expr)
        types = TYPES.copy()
        types.update(fn_types(functions))
        return check(expr, types)

    def assertRef(self, node, ref):
        with ref_eq_patcher():
            self.assertEqual(node.__ref__, ref)

    def testField(self):
        expr = self.check(S.f)
        self.assertRef(expr, NamedRef(None, 'f', TYPES['f']))

    def testEdgeField(self):
        expr = self.check(S.x.a)
        self.assertRef(expr, NamedRef(NamedRef(None, 'x', TYPES['x']),
                                      'a', TYPES['x'].fields['a']))
