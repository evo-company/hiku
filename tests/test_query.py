import difflib
from textwrap import dedent
from unittest import TestCase

import astor

from hiku.nodes import Tuple, Symbol
from hiku.query import merge, Edge, Field, Link, qualified_reqs, this, Ref
from hiku.query import RequirementsExtractor, ExpressionCompiler

from .base import reqs_eq_patcher


def foo(a, b):
    print('foo', a, b)

foo.__requires__ = [[Field('a1'), Field('a2')],
                    [Field('b1'), Field('b2')]]


def bar(c, d):
    print('bar', c, d)

bar.__requires__ = [[Field('c1'), Field('c2')],
                    [Field('d1'), Field('d2')]]


ENV = {
    'foo': foo,
    'bar': bar,
}


class TestQueryRequirements(TestCase):

    def assertRequires(self, node, requirements):
        re = RequirementsExtractor(ENV)
        re.visit(node)
        with reqs_eq_patcher():
            self.assertEqual(re.get_requirements(), requirements)

    def testMerge(self):
        with reqs_eq_patcher():
            self.assertEqual(
                merge([
                    Edge([Field('a1'), Field('a2'),
                          Link('b', Edge([Field('b1'), Field('b2')]))]),
                    Edge([Field('a2'), Field('a3'),
                          Link('b', Edge([Field('b2'), Field('b3')]))]),
                ]),
                Edge([Field('a1'), Field('a2'), Field('a3'),
                      Link('b', Edge([Field('b1'), Field('b2'),
                                      Field('b3')]))]),
            )

    def testQualifiedReqs(self):
        with reqs_eq_patcher():
            self.assertEqual(
                qualified_reqs(this, [Field('a'), Field('b')]),
                Edge([Field('a'), Field('b')]),
            )

        with reqs_eq_patcher():
            self.assertEqual(
                qualified_reqs(Ref(this, 'foo'),
                               [Field('a'), Field('b')]),
                Edge([Link('foo', Edge([Field('a'), Field('b')]))]),
            )

        with reqs_eq_patcher():
            self.assertEqual(
                qualified_reqs(Ref(Ref(this, 'foo'), 'bar'),
                               [Field('a'), Field('b')]),
                Edge([
                    Link('foo', Edge([
                        Link('bar', Edge([
                            Field('a'),
                            Field('b'),
                        ])),
                    ])),
                ]),
            )

    def testTuple(self):
        self.assertRequires(
            Tuple([Symbol('foo'), Symbol('this')]),
            Edge([Field('a1'), Field('a2')]),
        )

    def testGetExpr(self):
        self.assertRequires(
            Tuple([Symbol('foo'), Symbol('this'),
                   Tuple([Symbol('get'), Symbol('this'), Symbol('b')])]),
            Edge([Field('a1'), Field('a2'),
                  Link('b', Edge([Field('b1'), Field('b2')]))]),
        )

    def testIfExpr(self):
        self.assertRequires(
            Tuple([
                Symbol('if'),
                Tuple([Symbol('foo'), Symbol('this'), Symbol('this')]),
                Tuple([Symbol('bar'), Symbol('this'), Symbol('this')]),
            ]),
            Edge([Field('a1'), Field('a2'), Field('b1'), Field('b2'),
                  Field('c1'), Field('c2'), Field('d1'), Field('d2')]),
        )

    def testEachExpr(self):
        self.assertRequires(
            Tuple([
                Symbol('each'),
                Symbol('x'),
                Tuple([Symbol('get'), Symbol('this'), Symbol('link')]),
                Tuple([Symbol('foo'), Symbol('x'),
                       Tuple([Symbol('get'), Symbol('x'), Symbol('b')])]),
            ]),
            Edge([
                Link('link', Edge([
                    Field('a1'), Field('a2'),
                    Link('b', Edge([
                        Field('b1'),
                        Field('b2'),
                    ])),
                ])),
            ]),
        )


class TestQueryCompilation(TestCase):

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
