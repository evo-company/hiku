from contextlib import contextmanager
from collections import deque

from . import graph, query
from .refs import NamedRef, Ref
from .nodes import NodeTransformer, Symbol, Keyword, Tuple
from .types import RecordType, ListType, DictType, FunctionType
from .typedef.types import TypeRef, UnknownType


def _graph_to_types(obj):
    if isinstance(obj, graph.Edge):
        return RecordType((f.name, _graph_to_types(f))
                          for f in obj.fields.values())
    elif isinstance(obj, graph.Link):
        if obj.to_list:
            return ListType(TypeRef(obj.edge))
        else:
            return TypeRef(obj.edge)
    elif isinstance(obj, graph.Field):
        return obj.type or UnknownType()
    else:
        raise TypeError(type(obj))


def graph_types(obj):
    return {name: field
            for name, field in _graph_to_types(obj).fields.items()}


def _query_to_types(obj):
    if isinstance(obj, query.Edge):
        return RecordType((f.name, _query_to_types(f))
                          for f in obj.fields.values())
    elif isinstance(obj, query.Link):
        return _query_to_types(obj.edge)
    elif isinstance(obj, query.Field):
        return UnknownType()
    else:
        raise TypeError(type(obj))


def fn_types(functions):
    return {
        fn.__fn_name__: FunctionType([
            _query_to_types(r) if r is not None else UnknownType()
            for r in fn.__requires__
        ])
        for fn in functions
    }


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


def get_type(types, obj):
    if isinstance(obj, TypeRef):
        return types[obj.name]
    else:
        return obj


def node_type(types, node):
    return get_type(types, node.__ref__.to)


def check_type(types, t1, t2):
    t1 = get_type(types, t1)
    t2 = get_type(types, t2)
    if isinstance(t2, UnknownType):
        pass
    else:
        if isinstance(t1, type(t2)):
            if isinstance(t2, ListType):
                check_type(types, t1.item_type, t2.item_type)
            elif isinstance(t2, DictType):
                check_type(types, t1.key_type, t2.key_type)
                check_type(types, t1.value_type, t2.value_type)
            elif isinstance(t2, RecordType):
                for key, v2 in t2.fields.items():
                    v1 = t1.fields.get(key)
                    if v1 is None:
                        raise TypeError('Missing field {}'.format(key))
                    v1 = get_type(types, v1)
                    check_type(types, v1, v2)
        else:
            raise TypeError('Types mismatch: {} != {}'
                            .format(type(t1), type(t2)))


class Checker(NodeTransformer):

    def __init__(self, types):
        self.types = types
        self.env = Environ(types)

    def visit_get_expr(self, node):
        sym, obj, name = node.values
        assert isinstance(name, Symbol), type(name)
        obj = self.visit(obj)
        assert hasattr(obj, '__ref__'), 'Object does not have a reference'

        ref_to = node_type(self.types, obj)
        check_type(self.types, ref_to, RecordType({name.name: UnknownType()}))

        res = ref_to.fields.get(name.name)
        assert res is not None, 'Undefined field name: {}'.format(name.name)
        tup = Tuple([sym, obj, name])
        tup.__ref__ = NamedRef(obj.__ref__, name.name, res)
        return tup

    def visit_each_expr(self, node):
        var, col, expr = node.values[1:]
        assert isinstance(var, Symbol), repr(var)
        col = self.visit(col)
        assert hasattr(col, '__ref__'), 'Object does not have a reference'
        col_type = node_type(self.types, col)
        check_type(self.types, col_type, ListType(RecordType({})))
        var = Symbol(var.name)
        var.__ref__ = Ref(col.__ref__, col_type.item_type)
        with self.env.push({var.name: var.__ref__}):
            expr = self.visit(expr)
        return Tuple([Symbol('each'), var, col, expr])

    def visit_tuple_generic(self, node):
        sym = self.visit(node.values[0])
        assert isinstance(sym, Symbol), type(sym)
        args = [self.visit(val) for val in node.values[1:]]
        fn_type = node_type(self.types, sym)
        assert len(fn_type.arg_types) == len(args), 'Wrong arguments count'
        for arg, arg_type in zip(args, fn_type.arg_types):
            ref = getattr(arg, '__ref__', None)
            if ref is not None:
                check_type(self.types, node_type(self.types, arg), arg_type)
            else:
                check_type(self.types, UnknownType(), arg_type)
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
        assert node.name in self.env, 'Unknown symbol {}'.format(node.name)
        sym.__ref__ = self.env[node.name]
        return sym

    def visit_dict(self, node):
        assert not len(node.values) % 2, 'Probably missing keyword value'
        keys = node.values[::2]
        assert all(isinstance(k, Keyword) for k in keys), 'Wrong arguments'
        return super(Checker, self).visit_dict(node)


def check(expr, types):
    return Checker(types).visit(expr)
