from unittest import TestCase

from hiku.dsl import define, S, if_, each
from hiku.query import merge, Edge, Field, Link, qualified_reqs, this, Ref
from hiku.query import RequirementsExtractor

from .base import reqs_eq_patcher


@define('[[:a1 :a2] [:b1 :b2]]')
def foo(a, b):
    print('foo', a, b)


@define('[[:c1 :c2] [:d1 :d2]]')
def bar(c, d):
    print('bar', c, d)


ENV = {
    foo.__fn_name__: foo,
    bar.__fn_name__: bar,
}


class TestQuery(TestCase):

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
                qualified_reqs(this, Edge([Field('a'), Field('b')])),
                Edge([Field('a'), Field('b')]),
            )

        with reqs_eq_patcher():
            self.assertEqual(
                qualified_reqs(Ref(this, 'foo'),
                               Edge([Field('a'), Field('b')])),
                Edge([Link('foo', Edge([Field('a'), Field('b')]))]),
            )

        with reqs_eq_patcher():
            self.assertEqual(
                qualified_reqs(Ref(Ref(this, 'foo'), 'bar'),
                               Edge([Field('a'), Field('b')])),
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
            foo(S.this, S.this),
            Edge([Field('a1'), Field('a2'), Field('b1'), Field('b2')]),
        )

    def testGetExpr(self):
        self.assertRequires(
            foo(S.this, S.this.b),
            Edge([Field('a1'), Field('a2'),
                  Link('b', Edge([Field('b1'), Field('b2')]))]),
        )

    def testIfExpr(self):
        self.assertRequires(
            if_(1, foo(S.this, S.this), bar(S.this, S.this)),
            Edge([Field('a1'), Field('a2'), Field('b1'), Field('b2'),
                  Field('c1'), Field('c2'), Field('d1'), Field('d2')]),
        )

    def testEachExpr(self):
        self.assertRequires(
            each(S.x, S.this.link,
                 foo(S.x, S.x.b)),
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

    def testList(self):
        self.assertRequires(
            each(S.x, S.this.link,
                 [foo(S.x, S.x), bar(S.x, S.x)]),
            Edge([
                Link('link', Edge([
                    Field('a1'), Field('a2'), Field('b1'), Field('b2'),
                    Field('c1'), Field('c2'), Field('d1'), Field('d2'),
                ])),
            ]),
        )

    def testDict(self):
        self.assertRequires(
            each(S.x, S.this.link,
                 {'foo-value': foo(S.x, S.x),
                  'bar-value': bar(S.x, S.x)}),
            Edge([
                Link('link', Edge([
                    Field('a1'), Field('a2'), Field('b1'), Field('b2'),
                    Field('c1'), Field('c2'), Field('d1'), Field('d2'),
                ])),
            ]),
        )
