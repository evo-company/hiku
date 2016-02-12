from unittest import TestCase

from hiku import graph
from hiku.expr import define, S, each, to_expr
from hiku.refs import Ref, NamedRef, ref_to_req, RequirementsExtractor
from hiku.query import Edge, Field, Link
from hiku.checker import check

from .base import reqs_eq_patcher


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


class TestRefToReq(TestCase):

    def assertReq(self, ref, req, add_req=None):
        with reqs_eq_patcher():
            self.assertEqual(ref_to_req(ref, add_req), req)

    def testField(self):
        self.assertReq(NamedRef(None, 'f', Env.f),
                       Edge([Field('f')]))

    def testEdgeField(self):
        x_ref = NamedRef(None, 'x', Env.x)
        self.assertReq(x_ref,
                       Edge([Link('x', Edge([]))]))

        a_ref = NamedRef(x_ref, 'a', Env.x.fields['a'])
        self.assertReq(a_ref,
                       Edge([Link('x', Edge([Field('a')]))]))

    def testLinkOneEdgeField(self):
        x1_ref = NamedRef(None, 'x1', Env.x1)
        self.assertReq(x1_ref,
                       Edge([Link('x1', Edge([]))]))

        x_ref = Ref(x1_ref, Env.x)
        self.assertReq(x_ref,
                       Edge([Link('x1', Edge([]))]))

        b_ref = NamedRef(x_ref, 'b', Env.x.fields['b'])
        self.assertReq(b_ref,
                       Edge([Link('x1', Edge([Field('b')]))]))

    def testLinkListEdgeField(self):
        xs_ref = NamedRef(None, 'xs', Env.xs)
        self.assertReq(xs_ref,
                       Edge([Link('xs', Edge([]))]))

        x_ref = Ref(xs_ref, Env.x)
        self.assertReq(x_ref,
                       Edge([Link('xs', Edge([]))]))

        c_ref = NamedRef(x_ref, 'c', Env.x.fields['c'])
        self.assertReq(c_ref,
                       Edge([Link('xs', Edge([Field('c')]))]))

    def testAddReq(self):
        self.assertReq(NamedRef(None, 'xs', Env.xs),
                       Edge([Link('xs', Edge([Field('a'), Field('c')]))]),
                       add_req=Edge([Field('a'), Field('c')]))


class TestQuery(TestCase):

    def assertRequires(self, expr, reqs):
        fn_reg = {}
        expr = to_expr(expr, fn_reg)
        env = dict(_ENV, **{fn.__fn_name__: fn for fn in fn_reg.values()})
        expr = check(env, expr)
        expr_reqs = RequirementsExtractor.extract(env, expr)
        with reqs_eq_patcher():
            self.assertEqual(expr_reqs, reqs)

    def testField(self):
        self.assertRequires(S.f, Edge([Field('f')]))

    def testLinkField(self):
        self.assertRequires(
            S.x1.a,
            Edge([Link('x1', Edge([Field('a')]))]),
        )

    def testEdgeLinkField(self):
        self.assertRequires(
            S.y.x1.b,
            Edge([Link('y', Edge([Link('x1', Edge([Field('b')]))]))]),
        )

    def testEachLinkField(self):
        self.assertRequires(
            each(S.item, S.xs, S.item.a),
            Edge([Link('xs', Edge([Field('a')]))]),
        )

    def testEdgeEachLinkField(self):
        self.assertRequires(
            each(S.item, S.y.xs, S.item.b),
            Edge([Link('y', Edge([Link('xs', Edge([Field('b')]))]))]),
        )

    def testTupleWithEdges(self):
        self.assertRequires(
            foo(S.x, S.y),
            Edge([Link('x', Edge([Field('a'), Field('c')])),
                  Link('y', Edge([Field('d'), Field('f')]))]),
        )

    def testTupleWithLinks(self):
        self.assertRequires(
            foo(S.x1, S.y1),
            Edge([Link('x1', Edge([Field('a'), Field('c')])),
                  Link('y1', Edge([Field('d'), Field('f')]))]),
        )
        self.assertRequires(
            each(S.item, S.xs, foo(S.item, S.y1)),
            Edge([Link('xs', Edge([Field('a'), Field('c')])),
                  Link('y1', Edge([Field('d'), Field('f')]))]),
        )
        self.assertRequires(
            each(S.item, S.ys, foo(S.x1, S.item)),
            Edge([Link('x1', Edge([Field('a'), Field('c')])),
                  Link('ys', Edge([Field('d'), Field('f')]))]),
        )
        self.assertRequires(
            each(S.item, S.ys, foo(S.item.x1, S.item)),
            Edge([Link('ys', Edge([Field('d'), Field('f'),
                                   Link('x1', Edge([Field('a'),
                                                    Field('c')]))]))]),
        )

    def testTupleWithNestedLinkToOne(self):
        self.assertRequires(
            bar(S.y),
            Edge([Link('y',
                       Edge([Field('e'),
                             Link('x1', Edge([Field('b')]))]))]),
        )
        self.assertRequires(
            each(S.item, S.ys, bar(S.item)),
            Edge([Link('ys',
                       Edge([Field('e'),
                             Link('x1', Edge([Field('b')]))]))]),
        )

    def testTupleWithNestedLinkToMany(self):
        self.assertRequires(
            baz(S.y),
            Edge([Link('y',
                       Edge([Field('e'),
                             Link('xs', Edge([Field('b')]))]))]),
        )
        self.assertRequires(
            each(S.item, S.ys, baz(S.item)),
            Edge([Link('ys',
                       Edge([Field('e'),
                             Link('xs', Edge([Field('b')]))]))]),
        )

    def testTupleWithSimpleArgs(self):
        self.assertRequires(
            buz(S.x, 1, S.y, 2),
            Edge([Link('x', Edge([Field('a'), Field('c')])),
                  Link('y', Edge([Field('d'), Field('f')]))]),
        )

    def testList(self):
        self.assertRequires(
            each(S.item, S.ys,
                 [foo(S.item.x1, S.item), bar(S.item)]),
            Edge([
                Link('ys', Edge([
                    Field('d'), Field('e'), Field('f'),
                    Link('x1', Edge([Field('a'), Field('b'), Field('c')])),
                ])),
            ]),
        )

    def testDict(self):
        self.assertRequires(
            each(S.item, S.ys,
                 {'foo-value': foo(S.item.x1, S.item),
                  'bar-value': bar(S.item)}),
            Edge([
                Link('ys', Edge([
                    Field('d'), Field('e'), Field('f'),
                    Link('x1', Edge([Field('a'), Field('b'), Field('c')])),
                ])),
            ]),
        )
