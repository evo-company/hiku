import difflib
from textwrap import dedent
from unittest import TestCase

import astor

from hiku.nodes import Tuple, Symbol
from hiku.compiler import ExpressionCompiler


class TestCompiler(TestCase):

    def assertCompiles(self, expr, code):
        ec = ExpressionCompiler()
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
            Tuple([Symbol('foo'), Symbol('this'), Symbol('this')]),
            """
            env.foo(this, this)
            """
        )
