from unittest import TestCase

from hiku.nodes import Tuple, Symbol
from hiku.query import merge, Edge, Field, Link, qualified_reqs, this, Ref

from .base import reqs_eq_patcher


def foo(a):
    print('foo', a)

foo.__requires__ = [['a1', 'a2']]


ENV = {
    'foo': foo,
}


class RequirementsExtractor(object):

    def __init__(self, env):
        self.env = env
        self.requirements = []

    def _add_requirements(self, ref, reqs):
        _reqs = self.requirements
        if ref is this:
            _reqs.extend(reqs)

    def visit(self, node):
        if hasattr(node, 'accept'):
            return node.accept(self)
        else:
            return self.generic_visit(node)

    def generic_visit(self, node):
        return node

    def visit_tuple(self, node):
        sym = node.values[0]
        args = [self.visit(val) for val in node.values[1:]]
        fn = self.env[sym.name]
        fn_reqs = fn.__requires__
        for arg, arg_reqs in zip(args, fn_reqs):
            self._add_requirements(arg.__ref__, arg_reqs)
        return Tuple([sym] + args)

    def visit_symbol(self, node):
        sym = Symbol(node.name)
        assert sym.name == 'this', sym
        sym.__ref__ = this
        return sym


class TestRequirements(TestCase):

    def assertRequires(self, node, requirements):
        re = RequirementsExtractor(ENV)
        re.visit(node)
        self.assertEqual(re.requirements, requirements)

    def testTuple(self):
        self.assertRequires(
            Tuple([Symbol('foo'), Symbol('this')]),
            ['a1', 'a2'],
        )

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
