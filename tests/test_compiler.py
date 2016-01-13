from __future__ import unicode_literals

import difflib
from textwrap import dedent
from unittest import TestCase
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import astor

from hiku import query, graph
from hiku.dsl import define, S, if_, each, to_expr
from hiku.compat import PY3
from hiku.engine import Engine
from hiku.compiler import ExpressionCompiler
from hiku.sources.graph import subquery_fields
from hiku.readers.simple import read
from hiku.executors.thread import ThreadExecutor


@define(_name='foo')
def foo():
    pass


@define(_name='baz')
def baz():
    pass


class TestCompiler(TestCase):

    def assertCompiles(self, expr, code):
        ec = ExpressionCompiler({'foo', 'baz'})
        py_expr = ec.visit(to_expr(expr))
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

    def testSubQuery(self):
        thread_pool = ThreadPoolExecutor(2)
        e = Engine(ThreadExecutor(thread_pool))

        def query_a(fields, ids):
            data = {1: {'f': 2}}
            return [[data[i][f] for f in fields] for i in ids]

        r = graph.Edge(None, [
            graph.Edge('a', [
                graph.Field('f', query_a),
            ]),
        ])

        # ----------------------------------------------

        @define(query.Edge([query.Field('f')]), _name='inc_f')
        def inc_f(obj):
            return obj['f'] + 1

        r1 = graph.Edge(None, [
            graph.Edge('a1', subquery_fields(r, 'a', [inc_f], {
                'f1': inc_f(S.this),
            })),
            graph.Link('la1', None, 'a1', lambda: [1], True),
        ])

        self.assertEqual(e.execute(r1, read('[{:la1 [:f1]}]'))['la1'],
                         [{'f1': 3}])
