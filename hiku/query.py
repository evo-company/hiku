from itertools import chain
from collections import defaultdict

from .nodes import Symbol, Tuple


this = object()


class Ref(object):

    def __init__(self, backref, name):
        self.backref = backref
        self.name = name


class Field(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return ':{}'.format(self.name)


class Link(object):

    def __init__(self, name, edge):
        self.name = name
        self.edge = edge

    def __repr__(self):
        return '{{:{} {!r}}}'.format(self.name, self.edge)


class Edge(object):

    def __init__(self, fields):
        self.fields = {f.name: f for f in fields}

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self.fields.values())))


def _merge(edges):
    to_merge = defaultdict(list)
    for field in chain.from_iterable(e.fields.values() for e in edges):
        if field.__class__ is Link:
            to_merge[field.name].append(field.edge)
        else:
            yield field
    for name, values in to_merge.items():
        yield Link(name, Edge(_merge(values)))


def merge(edges):
    return Edge(_merge(edges))


def qualified_reqs(ref, reqs):
    edge = Edge(reqs)
    while ref is not this:
        edge = Edge([Link(ref.name, edge)])
        ref = ref.backref
    return edge


def if_(test, then_, else_):
    pass

if_.__requires__ = [None, None, None]


BUILTINS = {'if': if_}


class RequirementsExtractor(object):

    def __init__(self, env):
        self.env = dict(BUILTINS, **env)
        self._requirements = []

    def get_requirements(self):
        return merge(self._requirements)

    def visit(self, node):
        if hasattr(node, 'accept'):
            return node.accept(self)
        else:
            return self.generic_visit(node)

    def generic_visit(self, node):
        return node

    def visit_get_expr(self, node):
        sym, obj, name = node.values
        assert isinstance(name, Symbol)
        obj = self.visit(obj)
        assert hasattr(obj, '__ref__'), 'Object does not have a reference'
        tup = Tuple([sym, obj, name])
        tup.__ref__ = Ref(obj.__ref__, name.name)
        return tup

    def visit_tuple(self, node):
        sym = node.values[0]
        if sym.name == 'get':
            return self.visit_get_expr(node)
        else:
            args = [self.visit(val) for val in node.values[1:]]
            fn = self.env[sym.name]
            fn_reqs = fn.__requires__
            for arg, arg_reqs in zip(args, fn_reqs):
                if arg_reqs is not None:
                    self._requirements.append(qualified_reqs(arg.__ref__,
                                                             arg_reqs))
            return Tuple([sym] + args)

    def visit_symbol(self, node):
        sym = Symbol(node.name)
        assert sym.name == 'this', sym
        sym.__ref__ = this
        return sym
