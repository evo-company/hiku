from contextlib import contextmanager
from collections import deque

from . import graph, query
from .refs import NamedRef, Ref
from .nodes import NodeTransformer, Symbol, Keyword, Tuple


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
        if isinstance(req, query.Edge):
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
        elif isinstance(req, query.Link):
            assert isinstance(arg, graph.Link), type(arg)
            assert arg.entity in self.edges, arg.entity
            self.check_arg(req.edge, self.edges[arg.entity])
        elif isinstance(req, query.Field):
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


def check(env, expr):
    return Checker(env).visit(expr)
