from __future__ import unicode_literals

import difflib
from textwrap import dedent
from unittest import TestCase
from collections import OrderedDict

import astor

from hiku.dsl import define, S, if_, each, to_expr
from hiku.compat import PY3
from hiku.compiler import ExpressionCompiler


@define(_name='foo')
def foo():
    pass


@define(_name='baz')
def baz():
    pass


class TestCompiler(TestCase):

    def assertCompiles(self, expr, code):
        ec = ExpressionCompiler({'foo', 'baz'})
        py_expr = ec.visit(to_expr(expr, {}))
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
            foo(S.bar),
            """
            env['foo'](ctx['bar'])
            """
        )

    def testGetExpr(self):
        self.assertCompiles(
            foo(S.bar.baz),
            """
            env['foo'](ctx['bar']['baz'])
            """
        )

    def testIfExpr(self):
        self.assertCompiles(
            if_(1, foo(S.bar), baz(S.bar)),
            """
            (env['foo'](ctx['bar']) if 1 else env['baz'](ctx['bar']))
            """
        )

    def testEachExpr(self):
        self.assertCompiles(
            each(S.x, S.col,
                 foo(S.x, S.x.a)),
            """
            [env['foo'](x, x['a']) for x in ctx['col']]
            """
        )

    def testList(self):
        self.assertCompiles(
            [foo(1), baz(2)],
            """
            [env['foo'](1), env['baz'](2)]
            """
        )

    def testDict(self):
        self.assertCompiles(
            OrderedDict([('foo-value', foo(1)),
                         ('baz-value', baz(2))]),
            """
            {'foo-value': env['foo'](1), 'baz-value': env['baz'](2), }
            """
        )
