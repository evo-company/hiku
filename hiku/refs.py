from .query import Edge, Link, Field, merge
from .types import RecordType, ListType, Type, ContainerType
from .nodes import NodeVisitor
from .typedef.types import UnknownType, TypeRef


class Ref(object):

    def __init__(self, backref, to):
        self.backref = backref
        self.to = to


class NamedRef(Ref):

    def __init__(self, backref, name, to):
        super(NamedRef, self).__init__(backref, to)
        self.name = name


def get_type(types, type_):
    return types[type_.name] if isinstance(type_, TypeRef) else type_


def ref_to_req(types, ref, add_req=None):
    if ref is None:
        assert add_req is not None
        return add_req

    ref_type = get_type(types, ref.to)

    if isinstance(ref_type, RecordType):
        if isinstance(ref, NamedRef):
            edge = Edge([]) if add_req is None else add_req
            return ref_to_req(types, ref.backref,
                              Edge([Link(ref.name, edge)]))
        else:
            return ref_to_req(types, ref.backref, add_req)

    elif isinstance(ref_type, ListType):
        item_type = get_type(types, ref_type.item_type)
        if isinstance(item_type, RecordType):
            assert isinstance(ref, NamedRef), type(ref)
            edge = Edge([]) if add_req is None else add_req
            return ref_to_req(types, ref.backref,
                              Edge([Link(ref.name, edge)]))
        else:
            raise NotImplementedError

    elif isinstance(ref_type, (Type, UnknownType)):
        assert not isinstance(ref_type, ContainerType)
        assert isinstance(ref, NamedRef), type(ref)
        assert add_req is None, repr(add_req)
        return ref_to_req(types, ref.backref,
                          Edge([Field(ref.name)]))

    else:
        raise TypeError('Reference to the invalid type: {!r}'
                        .format(ref_type))


def type_to_query(type_):
    fields = []
    for f_name, f_type in type_.fields.items():
        if isinstance(f_type, RecordType):
            fields.append(Link(f_name, type_to_query(f_type)))
        elif isinstance(f_type, ListType):
            if isinstance(f_type.item_type, RecordType):
                fields.append(Link(f_name, type_to_query(f_type.item_type)))
            else:
                raise NotImplementedError
        else:
            fields.append(Field(f_name))
    return Edge(fields)


class RequirementsExtractor(NodeVisitor):

    def __init__(self, types):
        self._types = types
        self._reqs = []

    @classmethod
    def extract(cls, types, expr):
        extractor = cls(types)
        extractor.visit(expr)
        return merge(extractor._reqs)

    def visit(self, node):
        ref = getattr(node, '__ref__', None)
        if ref is not None:
            req = ref_to_req(self._types, ref)
            if req is not None:
                self._reqs.append(req)
        super(RequirementsExtractor, self).visit(node)

    def visit_tuple(self, node):
        sym, args = node.values[0], node.values[1:]
        sym_ref = getattr(sym, '__ref__', None)
        if sym_ref is not None:
            for arg, arg_type in zip(args, sym_ref.to.arg_types):
                if isinstance(arg_type, RecordType):
                    self._reqs.append(ref_to_req(self._types, arg.__ref__,
                                                 type_to_query(arg_type)))
                else:
                    self.visit(arg)
        else:
            for arg in args:
                self.visit(arg)
