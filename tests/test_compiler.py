from __future__ import unicode_literals

import difflib
from textwrap import dedent
from unittest import TestCase
from collections import OrderedDict

import astor

from hiku.expr import define, S, if_, each, to_expr
from hiku.graph import Graph, Field, Edge, Link
from hiku.compat import PY3
from hiku.checker import check, graph_types, fn_types
from hiku.compiler import ExpressionCompiler


@define('[nil]', _name='foo')
def foo(value):
    pass


@define('[nil]', _name='bar')
def bar(value):
    pass


@define('[nil [:c]]', _name='baz')
def baz(a, y):
    pass


def noop(*_):
    return 1/0


ENV = Graph([
    Field('a', noop),
    Edge('x', [
        Field('b', noop),
    ]),
    Edge('y', [
        Field('c', noop),
        Link('x1', None, 'x', noop, to_list=False),
        Link('xs', None, 'x', noop, to_list=True),
    ]),
    Link('y1', None, 'y', noop, to_list=False),
    Link('ys', None, 'y', noop, to_list=True),
])


class TestCompiler(TestCase):

    def assertCompiles(self, dsl_expr, code):
        expr, functions = to_expr(dsl_expr)

        types = graph_types(ENV)
        types.update(fn_types(functions))

        expr = check(expr, types)

        py_expr = ExpressionCompiler.compile_expr(expr)

        first = astor.to_source(py_expr)
        if not PY3:
            first = first.replace("u'", "'")
        second = dedent(code).strip()
        if first != second:
            msg = ('Compiled code is not equal:\n\n{}'
                   .format('\n'.join(difflib.ndiff(first.splitlines(),
                                                   second.splitlines()))))
            raise self.failureException(msg)

    def testTuple(self):
        self.assertCompiles(
            foo(S.a),
            """
            env['foo'](ctx['a'])
            """
        )

    def testGetExpr(self):
        self.assertCompiles(
            foo(S.x.b),
            """
            env['foo'](ctx['x']['b'])
            """
        )

    def testIfExpr(self):
        self.assertCompiles(
            if_(1, foo(S.a), bar(S.a)),
            """
            (env['foo'](ctx['a']) if 1 else env['bar'](ctx['a']))
            """
        )

    def testEachExpr(self):
        self.assertCompiles(
            each(S.i, S.ys,
                 baz(S.a, S.i)),
            """
            [env['baz'](ctx['a'], i) for i in ctx['ys']]
            """
        )

    def testNameCollision(self):
        self.assertCompiles(
            each(S.i, S.ys,
                 each(S.i, S.i.xs, bar(S.i.b))),
            """
            [[env['bar'](i_2['b']) for i_2 in i['xs']] for i in ctx['ys']]
            """
        )

    def testList(self):
        self.assertCompiles(
            [foo(1), bar(2)],
            """
            [env['foo'](1), env['bar'](2)]
            """
        )

    def testDict(self):
        self.assertCompiles(
            OrderedDict([('foo-value', foo(1)),
                         ('bar-value', bar(2))]),
            """
            {'foo-value': env['foo'](1), 'bar-value': env['bar'](2), }
            """
        )
