from ..query import Node, Link, Field, merge
from ..types import GenericMeta, RecordMeta, SequenceMeta, MappingMeta
from ..types import OptionalMeta, TypeRefMeta

from .nodes import NodeVisitor


# TODO: revisit this
_CONTAINER_TYPES = (
    OptionalMeta,
    SequenceMeta,
    MappingMeta,
    RecordMeta,
)


class Ref(object):

    def __init__(self, backref, to):
        self.backref = backref
        self.to = to


class NamedRef(Ref):

    def __init__(self, backref, name, to):
        super(NamedRef, self).__init__(backref, to)
        self.name = name


def get_type(types, type_):
    return (types[type_.__type_name__]
            if isinstance(type_, TypeRefMeta)
            else type_)


def ref_to_req(types, ref, add_req=None):
    if ref is None:
        assert add_req is not None
        return add_req

    ref_type = get_type(types, ref.to)
    if isinstance(ref_type, OptionalMeta):
        ref_type = get_type(types, ref_type.__type__)

    if isinstance(ref_type, RecordMeta):
        if isinstance(ref, NamedRef):
            node = Node([]) if add_req is None else add_req
            return ref_to_req(types, ref.backref,
                              Node([Link(ref.name, node)]))
        else:
            return ref_to_req(types, ref.backref, add_req)

    elif isinstance(ref_type, SequenceMeta):
        item_type = get_type(types, ref_type.__item_type__)
        if isinstance(item_type, RecordMeta):
            assert isinstance(ref, NamedRef), type(ref)
            node = Node([]) if add_req is None else add_req
            return ref_to_req(types, ref.backref,
                              Node([Link(ref.name, node)]))
        else:
            raise NotImplementedError

    elif isinstance(ref_type, GenericMeta):
        assert not isinstance(ref_type, _CONTAINER_TYPES)
        assert isinstance(ref, NamedRef), type(ref)
        assert add_req is None, repr(add_req)
        return ref_to_req(types, ref.backref,
                          Node([Field(ref.name)]))

    else:
        raise TypeError('Reference to the invalid type: {!r}'
                        .format(ref_type))


def type_to_query(type_):
    fields = []
    for f_name, f_type in type_.__field_types__.items():
        if isinstance(f_type, OptionalMeta):
            f_type = f_type.__type__
        if isinstance(f_type, RecordMeta):
            fields.append(Link(f_name, type_to_query(f_type)))
        elif isinstance(f_type, SequenceMeta):
            if isinstance(f_type.__item_type__, RecordMeta):
                fields.append(Link(f_name, type_to_query(f_type.__item_type__)))
            else:
                raise NotImplementedError
        else:
            fields.append(Field(f_name))
    return Node(fields)


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
            for arg, arg_type in zip(args, sym_ref.to.__arg_types__):
                if isinstance(arg_type, OptionalMeta):
                    arg_type = arg_type.__type__
                if isinstance(arg_type, RecordMeta):
                    self._reqs.append(ref_to_req(self._types, arg.__ref__,
                                                 type_to_query(arg_type)))
                else:
                    self.visit(arg)
        else:
            for arg in args:
                self.visit(arg)
