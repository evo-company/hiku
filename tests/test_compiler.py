import difflib
from textwrap import dedent
from unittest import TestCase

import astor

from hiku.nodes import Tuple, Symbol, List, Dict, Keyword
from hiku.compiler import ExpressionCompiler


class TestCompiler(TestCase):

    def assertCompiles(self, expr, code):
        ec = ExpressionCompiler({'foo', 'baz'})
        py_expr = ec.visit(expr)
        first = astor.to_source(py_expr)
        second = dedent(code).strip()
        if first != second:
            msg = ('Compiled code is not equal:\n\n{}'
                   .format('\n'.join(difflib.ndiff(first.splitlines(),
                                                   second.splitlines()))))
            raise self.failureException(msg)

    def testTuple(self):
        self.assertCompiles(
            Tuple([Symbol('foo'), Symbol('bar')]),
            """
            env['foo'](ctx['bar'])
            """
        )

    def testGetExpr(self):
        self.assertCompiles(
            Tuple([Symbol('foo'),
                   Tuple([Symbol('get'), Symbol('bar'), Symbol('baz')])]),
            """
            env['foo'](ctx['bar']['baz'])
            """
        )

    def testIfExpr(self):
        self.assertCompiles(
            Tuple([
                Symbol('if'),
                1,
                Tuple([Symbol('foo'), Symbol('bar')]),
                Tuple([Symbol('baz'), Symbol('bar')]),
            ]),
            """
            (env['foo'](ctx['bar']) if 1 else env['baz'](ctx['bar']))
            """
        )

    def testEachExpr(self):
        self.assertCompiles(
            Tuple([
                Symbol('each'),
                Symbol('x'),
                Symbol('col'),
                Tuple([Symbol('foo'), Symbol('x'),
                       Tuple([Symbol('get'), Symbol('x'), Symbol('a')])]),
            ]),
            """
            [env['foo'](x, x['a']) for x in ctx['col']]
            """
        )

    def testList(self):
        self.assertCompiles(
            List([
                Tuple([Symbol('foo'), 1]),
                Tuple([Symbol('baz'), 2]),
            ]),
            """
            [env['foo'](1), env['baz'](2)]
            """
        )

    def testDict(self):
        self.assertCompiles(
            Dict([
                Keyword('foo-value'), Tuple([Symbol('foo'), 1]),
                Keyword('baz-value'), Tuple([Symbol('baz'), 2]),
            ]),
            """
            {'foo-value': env['foo'](1), 'baz-value': env['baz'](2), }
            """
        )
