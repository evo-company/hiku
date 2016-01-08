from __future__ import unicode_literals

import difflib
from textwrap import dedent
from unittest import TestCase
from collections import OrderedDict

import astor

from hiku import query
from hiku.dsl import define, S, if_, each, to_expr
from hiku.query import RequirementsExtractor, export, merge
from hiku.compat import PY3
from hiku.engine import Query, store_fields
from hiku.reader import read
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
        from hiku.graph import Edge, Field, Link
        from hiku.engine import Engine
        from hiku.executors.thread import ThreadExecutor

        from concurrent.futures import ThreadPoolExecutor
        thread_pool = ThreadPoolExecutor(2)

        e = Engine(ThreadExecutor(thread_pool))

        def link_to_a():
            return [1]

        def query_a(fields, ids):
            return [[2]]

        r = Edge(None, [
            Edge('a', [
                Field('f', query_a),
            ]),
        ])

        # ----------------------------------------------

        @define(query.Edge([query.Field('f')]), _name='inc')
        def inc(obj):
            return obj['f'] + 1

        fn_env = {'inc': inc.fn}
        re_env = {'inc': inc}
        ec_env = {'inc'}

        exprs = {
            'f': inc(S.this),
        }

        ec = ExpressionCompiler(ec_env)

        reqs_map = {}
        procs_map = {}
        for name, expr in exprs.items():
            re = RequirementsExtractor(re_env)
            re.visit(expr)
            reqs_map[name] = re.get_requirements()
            procs_map[name] = eval(compile(ec.compile_lambda_expr(expr),
                                           '<expr>', 'eval'))

        def query_a1(queue, task_set, fields, ids):
            this_edge = 'a'

            reqs = export(merge(reqs_map[f.name] for f in fields))
            procs = [procs_map[f.name] for f in fields]

            query = Query(queue, task_set, r, None)
            this_link = Link('this', None, this_edge, None, True)
            query._process_link(r, this_link, reqs, None, ids)

            def result_proc(store):
                rows = []
                ctx = {}
                for this in query.result()['this']:
                    rows.append([proc(this, fn_env, ctx) for proc in procs])
                store_fields(store, r1.fields[this_edge], fields, ids, rows)

            return result_proc

        query_a1.__subquery__ = True

        r1 = Edge(None, [
            Edge('a', [
                Field('f', query_a1),
            ]),
            Link('la', None, 'a', link_to_a, True),
        ])

        self.assertEqual(e.execute(r1, read('[{:la [:f]}]'))['la'],
                         [{'f': 3}])
