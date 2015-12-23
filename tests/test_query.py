from unittest import TestCase

from hiku.nodes import Tuple, Symbol


this = object()


class Ref(object):

    def __init__(self, backref, name):
        self.backref = backref
        self.name = name


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
