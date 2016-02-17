from unittest import TestCase, skip

from hiku import graph
from hiku.expr import define, S, each, to_expr
from hiku.refs import Ref, NamedRef, ref_to_req, RequirementsExtractor
from hiku.query import Edge, Field, Link
from hiku.checker import check, graph_types, fn_types

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


ENV = graph.Edge(None, [
    graph.Field('f', noop),
    graph.Edge('x', [
        graph.Field('a', noop),
        graph.Field('b', noop),
        graph.Field('c', noop),
    ]),
    graph.Link('x1', None, 'x', noop, to_list=False),
    graph.Link('xs', None, 'x', noop, to_list=True),
    graph.Edge('y', [
        graph.Field('d', noop),
        graph.Field('e', noop),
        graph.Field('f', noop),
        graph.Link('x1', None, 'x', noop, to_list=False),
        graph.Link('xs', None, 'x', noop, to_list=True),
    ]),
    graph.Link('y1', None, 'y', noop, to_list=False),
    graph.Link('ys', None, 'y', noop, to_list=True),
])


TYPES = graph_types(ENV)


class TestRefToReq(TestCase):

    def assertReq(self, ref, req, add_req=None):
        with reqs_eq_patcher():
            self.assertEqual(ref_to_req(TYPES, ref, add_req), req)

    def testField(self):
        self.assertReq(NamedRef(None, 'f', TYPES['f']),
                       Edge([Field('f')]))

    def testEdgeField(self):
        x_ref = NamedRef(None, 'x', TYPES['x'])
        self.assertReq(x_ref,
                       Edge([Link('x', Edge([]))]))

        a_ref = NamedRef(x_ref, 'a', TYPES['x'].fields['a'])
        self.assertReq(a_ref,
                       Edge([Link('x', Edge([Field('a')]))]))

    def testLinkOneEdgeField(self):
        x1_ref = NamedRef(None, 'x1', TYPES['x1'])
        self.assertReq(x1_ref,
                       Edge([Link('x1', Edge([]))]))

        x_ref = Ref(x1_ref, TYPES['x'])
        self.assertReq(x_ref,
                       Edge([Link('x1', Edge([]))]))

        b_ref = NamedRef(x_ref, 'b', TYPES['x'].fields['b'])
        self.assertReq(b_ref,
                       Edge([Link('x1', Edge([Field('b')]))]))

    def testLinkListEdgeField(self):
        xs_ref = NamedRef(None, 'xs', TYPES['xs'])
        self.assertReq(xs_ref,
                       Edge([Link('xs', Edge([]))]))

        x_ref = Ref(xs_ref, TYPES['x'])
        self.assertReq(x_ref,
                       Edge([Link('xs', Edge([]))]))

        c_ref = NamedRef(x_ref, 'c', TYPES['x'].fields['c'])
        self.assertReq(c_ref,
                       Edge([Link('xs', Edge([Field('c')]))]))

    def testAddReq(self):
        self.assertReq(NamedRef(None, 'xs', TYPES['xs']),
                       Edge([Link('xs', Edge([Field('a'), Field('c')]))]),
                       add_req=Edge([Field('a'), Field('c')]))


class TestQuery(TestCase):

    def assertRequires(self, dsl_expr, reqs):
        expr, functions = to_expr(dsl_expr)
        types = graph_types(ENV)
        types.update(fn_types(functions))
        expr = check(expr, types)
        expr_reqs = RequirementsExtractor.extract(types, expr)
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

    @skip('fn_types() lacks information about links (single or list)')
    def testTupleWithNestedLinkToMany(self):
        self.assertRequires(
            baz(S.y),  # [[:e {:xs [:b]}]]
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
