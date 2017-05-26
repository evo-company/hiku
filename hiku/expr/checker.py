from contextlib import contextmanager
from collections import deque, OrderedDict

from .. import graph
from ..types import Sequence, SequenceMeta, Record, RecordMeta, Optional
from ..types import MappingMeta, OptionalMeta, Unknown, UnknownMeta
from ..types import TypeRef, TypeRefMeta

from .refs import NamedRef, Ref
from .nodes import NodeTransformer, Symbol, Keyword, Tuple, List


class GraphTypes(graph.GraphVisitor):

    def visit_graph(self, obj):
        types = OrderedDict((node.name, self.visit(node)) for node in obj.nodes)
        types.update(self.visit(obj.root).__field_types__)
        return types

    def visit_node(self, obj):
        return Record[[(f.name, self.visit(f)) for f in obj.fields]]

    def visit_root(self, obj):
        return Record[[(f.name, self.visit(f)) for f in obj.fields]]

    def visit_link(self, obj):
        if obj.type_enum is graph.Maybe:
            return Optional[TypeRef[obj.node]]
        elif obj.type_enum is graph.One:
            return TypeRef[obj.node]
        elif obj.type_enum is graph.Many:
            return Sequence[TypeRef[obj.node]]
        else:
            raise TypeError(repr(obj.type_enum))

    def visit_field(self, obj):
        return obj.type or Unknown


def graph_types(graph_):
    return GraphTypes().visit(graph_)


def fn_types(functions):
    return {fn.__def_name__: fn.__def_type__ for fn in functions}


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
    if isinstance(obj, TypeRefMeta):
        return types[obj.__type_name__]
    else:
        return obj


def node_type(types, node):
    return get_type(types, node.__ref__.to)


def check_type(types, t1, t2):
    t1 = get_type(types, t1)
    t2 = get_type(types, t2)
    if isinstance(t2, UnknownMeta):
        pass
    else:
        if isinstance(t1, type(t2)):
            if isinstance(t2, OptionalMeta):
                check_type(types, t1.__type__, t2.__type__)
            elif isinstance(t2, SequenceMeta):
                check_type(types, t1.__item_type__, t2.__item_type__)
            elif isinstance(t2, MappingMeta):
                check_type(types, t1.__key_type__, t2.__key_type__)
                check_type(types, t1.__value_type__, t2.__value_type__)
            elif isinstance(t2, RecordMeta):
                for key, v2 in t2.__field_types__.items():
                    v1 = t1.__field_types__.get(key)
                    if v1 is None:
                        raise TypeError('Missing field {}'.format(key))
                    v1 = get_type(types, v1)
                    check_type(types, v1, v2)
        elif isinstance(t2, OptionalMeta):
            check_type(types, t1, t2.__type__)
        else:
            raise TypeError('Types mismatch, {!r} != {!r}'.format(t1, t2))


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
        check_type(self.types, ref_to, Record[{name.name: Unknown}])

        res = ref_to.__field_types__.get(name.name)
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
        check_type(self.types, col_type, Sequence[Record[{}]])
        var = Symbol(var.name)
        var.__ref__ = Ref(col.__ref__, col_type.__item_type__)
        with self.env.push({var.name: var.__ref__}):
            expr = self.visit(expr)
        return Tuple([Symbol('each'), var, col, expr])

    def visit_if_some_expr(self, node):
        bind, then, else_ = node.values[1:]
        assert isinstance(bind, List) and len(bind.values) == 2, repr(bind)
        bind_sym, bind_expr = bind.values
        assert isinstance(bind_sym, Symbol), repr(bind_sym)
        bind_expr = self.visit(bind_expr)
        assert hasattr(bind_expr, '__ref__'), 'Object does not have a reference'
        bind_type = node_type(self.types, bind_expr)
        if isinstance(bind_type, OptionalMeta):
            bind_expr_ref = Ref(bind_expr.__ref__, bind_type.__type__)
        else:
            # TODO: warn about unnecessary check
            bind_expr_ref = bind_expr.__ref__
        bind_sym = Symbol(bind_sym.name)
        bind_sym.__ref__ = bind_expr_ref
        with self.env.push({bind_sym.name: bind_sym.__ref__}):
            then = self.visit(then)
        else_ = self.visit(else_)
        return Tuple([Symbol('if_some'), List([bind_sym, bind_expr]),
                      then, else_])

    def visit_tuple_generic(self, node):
        sym = self.visit(node.values[0])
        assert isinstance(sym, Symbol), type(sym)
        args = [self.visit(val) for val in node.values[1:]]
        fn_type = node_type(self.types, sym)
        assert len(fn_type.__arg_types__) == len(args), 'Wrong arguments count'
        for arg, arg_type in zip(args, fn_type.__arg_types__):
            ref = getattr(arg, '__ref__', None)
            if ref is not None:
                check_type(self.types, node_type(self.types, arg), arg_type)
            else:
                check_type(self.types, Unknown, arg_type)
        return Tuple([sym] + args)

    def visit_tuple(self, node):
        sym = node.values[0]
        if sym.name == 'get':
            return self.visit_get_expr(node)
        elif sym.name == 'each':
            return self.visit_each_expr(node)
        elif sym.name == 'if_some':
            return self.visit_if_some_expr(node)
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
