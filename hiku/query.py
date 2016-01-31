from itertools import chain
from contextlib import contextmanager
from collections import defaultdict, deque

from . import graph
from .nodes import Symbol, Tuple, Keyword, NodeVisitor, NodeTransformer


class Ref(object):

    def __init__(self, backref, to):
        self.backref = backref
        self.to = to


class NamedRef(Ref):

    def __init__(self, backref, name, to):
        super(NamedRef, self).__init__(backref, to)
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


class Environ(object):

    def __init__(self, values):
        env_vars = {}
        for name, value in values.items():
            env_vars[name] = NamedRef(None, name, value)
        self.vars = deque([env_vars])

    @contextmanager
    def push(self, mapping):
        self.vars.append(mapping)
        try:
            yield
        finally:
            self.vars.pop()

    def __getitem__(self, key):
        for d in reversed(self.vars):
            try:
                return d[key]
            except KeyError:
                continue
        else:
            raise KeyError(repr(key))

    def __contains__(self, key):
        return any(key in d for d in self.vars)


def ref_to_req(ref, add_req=None):
    if ref is None:
        assert add_req is not None
        return add_req

    elif isinstance(ref.to, graph.Field):
        assert isinstance(ref, NamedRef), type(ref)
        assert add_req is None, repr(add_req)
        return ref_to_req(ref.backref, Edge([Field(ref.name)]))

    elif isinstance(ref.to, graph.Edge):
        if isinstance(ref, NamedRef):
            edge = Edge([]) if add_req is None else add_req
            return ref_to_req(ref.backref, Edge([Link(ref.name, edge)]))
        else:
            return ref_to_req(ref.backref, add_req)

    elif isinstance(ref.to, graph.Link):
        assert isinstance(ref, NamedRef), type(ref)
        edge = Edge([]) if add_req is None else add_req
        return ref_to_req(ref.backref, Edge([Link(ref.name, edge)]))

    else:
        raise TypeError(type(ref.to))


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


class Checker(NodeTransformer):

    def __init__(self, env):
        self.edges = {item.name: item for item in env.values()
                      if isinstance(item, graph.Edge)}
        self.env = Environ(env)

    def visit_get_expr(self, node):
        obj, name = node.values[1:]
        assert isinstance(name, Symbol), type(name)
        obj = self.visit(obj)
        assert hasattr(obj, '__ref__'), 'Object does not have a reference'

        ref_to = obj.__ref__.to
        if isinstance(ref_to, graph.Edge):
            edge = obj.__ref__.to
            ref_to_edge = obj.__ref__

        elif isinstance(ref_to, graph.Link):
            assert not ref_to.to_list, 'Only links to one object possible'
            edge = self.edges[obj.__ref__.to.entity]
            ref_to_edge = Ref(obj.__ref__, edge)

        else:
            raise TypeError(repr(ref_to))

        res = edge.fields.get(name.name)
        assert res is not None, 'Undefined field name: {}'.format(name.name)
        tup = Tuple([Symbol('get'), obj, name])
        tup.__ref__ = NamedRef(ref_to_edge, name.name, res)
        return tup

    def visit_each_expr(self, node):
        var, col, expr = node.values[1:]
        assert isinstance(var, Symbol), repr(var)
        col = self.visit(col)
        assert hasattr(col, '__ref__'), 'Object does not have a reference'
        assert isinstance(col.__ref__.to, graph.Link) and \
            col.__ref__.to.to_list is True, type(col.__ref__.to)

        var = Symbol(var.name)
        var.__ref__ = Ref(col.__ref__, self.edges[col.__ref__.to.entity])
        with self.env.push({var.name: var.__ref__}):
            expr = self.visit(expr)
        return Tuple([Symbol('each'), var, col, expr])

    def check_arg(self, req, arg):
        if isinstance(req, Edge):
            if isinstance(arg, graph.Edge):
                edge = arg
            elif isinstance(arg, graph.Link):
                assert not arg.to_list
                edge = self.edges[arg.entity]
            else:
                raise TypeError(type(arg))
            for name, field in req.fields.items():
                assert name in edge.fields, name
                self.check_arg(field, edge.fields[name])
        elif isinstance(req, Link):
            assert isinstance(arg, graph.Link), type(arg)
            assert arg.entity in self.edges, arg.entity
            self.check_arg(req.edge, self.edges[arg.entity])
        elif isinstance(req, Field):
            assert isinstance(arg, graph.Field), type(arg)
        else:
            raise TypeError(type(req))

    def visit_tuple_generic(self, node):
        sym = node.values[0]
        args = [self.visit(val) for val in node.values[1:]]
        fn = self.env[sym.name].to
        fn_reqs = fn.__requires__
        for arg, arg_reqs in zip(args, fn_reqs):
            assert hasattr(arg, '__ref__'), 'Argument does not have a reference'
            self.check_arg(arg_reqs, arg.__ref__.to)
        return Tuple([sym] + args)

    def visit_tuple(self, node):
        sym = node.values[0]
        if sym.name == 'get':
            return self.visit_get_expr(node)
        elif sym.name == 'each':
            return self.visit_each_expr(node)
        else:
            return self.visit_tuple_generic(node)

    def visit_symbol(self, node):
        sym = Symbol(node.name)
        sym.__ref__ = self.env[node.name]
        return sym

    def visit_dict(self, node):
        assert not len(node.values) % 2, 'Probably missing keyword value'
        keys = node.values[::2]
        assert all(isinstance(k, Keyword) for k in keys), 'Wrong arguments'
        return super(Checker, self).visit_dict(node)


class RequirementsExtractor(NodeVisitor):

    def __init__(self, env):
        self.env = env
        self._reqs = []

    @classmethod
    def analyze(cls, env, expr):
        expr = Checker(env).visit(expr)
        extractor = cls(env)
        extractor.visit(expr)
        return merge(extractor._reqs)

    def visit(self, node):
        ref = getattr(node, '__ref__', None)
        if ref is not None:
            self._reqs.append(ref_to_req(ref))
        super(RequirementsExtractor, self).visit(node)

    def visit_tuple(self, node):
        sym, args = node.values[0], node.values[1:]
        if sym.name in self.env:
            for arg, req in zip(args, self.env[sym.name].__requires__):
                if req is None:
                    continue
                if isinstance(arg.__ref__.to, (graph.Edge, graph.Link)):
                    assert isinstance(req, Edge), type(req)
                    self._reqs.append(ref_to_req(arg.__ref__, req))
                else:
                    assert isinstance(arg.__ref__.to, graph.Field), \
                        type(arg.__ref__.to)
                    assert isinstance(req, None), repr(req)
        super(RequirementsExtractor, self).visit_tuple(node)
