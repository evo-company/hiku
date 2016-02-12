from hiku import graph
from hiku.expr import define, S, to_expr
from hiku.refs import NamedRef
from hiku.checker import check

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


class Env(object):
    f = graph.Field('f', noop)
    x = graph.Edge('x', [
        graph.Field('a', noop),
        graph.Field('b', noop),
        graph.Field('c', noop),
    ])
    x1 = graph.Link('x1', None, 'x', noop, to_list=False)
    xs = graph.Link('xs', None, 'x', noop, to_list=True)
    y = graph.Edge('y', [
        graph.Field('d', noop),
        graph.Field('e', noop),
        graph.Field('f', noop),
        graph.Link('x1', None, 'x', noop, to_list=False),
        graph.Link('xs', None, 'x', noop, to_list=True),
    ])
    y1 = graph.Link('y1', None, 'y', noop, to_list=False)
    ys = graph.Link('ys', None, 'y', noop, to_list=True)


_ENV = {i.name: i
        for i in [Env.f, Env.x, Env.x1, Env.xs, Env.y, Env.y1, Env.ys]}

_ENV[foo.__fn_name__] = foo
_ENV[bar.__fn_name__] = bar
_ENV[baz.__fn_name__] = baz


class TestChecker(TestCase):

    def check(self, expr):
        fn_reg = {}
        expr = to_expr(expr, fn_reg)
        env = dict(_ENV, **{fn.__fn_name__: fn for fn in fn_reg.values()})
        return check(env, expr)

    def assertRef(self, node, ref):
        with ref_eq_patcher():
            self.assertEqual(node.__ref__, ref)

    def testField(self):
        expr = self.check(S.f)
        self.assertRef(expr, NamedRef(None, 'f', Env.f))

    def testEdgeField(self):
        expr = self.check(S.x.a)
        self.assertRef(expr, NamedRef(NamedRef(None, 'x', Env.x),
                                      'a', Env.x.fields['a']))
