from ..query import Node, Link, Field, merge
from ..types import GenericMeta, RecordMeta, SequenceMeta, MappingMeta
from ..types import OptionalMeta, get_type

from .nodes import NodeVisitor


# TODO: revisit this
_CONTAINER_TYPES = (
    OptionalMeta,
    SequenceMeta,
    MappingMeta,
    RecordMeta,
)


class Ref:
    def __init__(self, backref, to):
        self.backref = backref
        self.to = to

    def __repr__(self):
        return "{!r} > {!r}".format(self.to, self.backref)

    def __eq__(self, other):
        return (
            self.__class__ is other.__class__
            and self.__dict__ == other.__dict__
        )

    def __ne__(self, other):
        return not self.__eq__(other)


class NamedRef(Ref):
    def __init__(self, backref, name, to):
        super(NamedRef, self).__init__(backref, to)
        self.name = name

    def __repr__(self):
        return "{}:{!r} > {!r}".format(self.name, self.to, self.backref)


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
            return ref_to_req(types, ref.backref, Node([Link(ref.name, node)]))
        else:
            return ref_to_req(types, ref.backref, add_req)

    elif isinstance(ref_type, SequenceMeta):
        item_type = get_type(types, ref_type.__item_type__)
        if isinstance(item_type, RecordMeta):
            assert isinstance(ref, NamedRef), type(ref)
            node = Node([]) if add_req is None else add_req
            return ref_to_req(types, ref.backref, Node([Link(ref.name, node)]))
        else:
            assert not isinstance(item_type, _CONTAINER_TYPES), ref_type
            assert isinstance(ref, NamedRef), type(ref)
            assert add_req is None, repr(add_req)
            return ref_to_req(types, ref.backref, Node([Field(ref.name)]))

    elif isinstance(ref_type, GenericMeta):
        assert not isinstance(ref_type, _CONTAINER_TYPES), ref_type
        assert add_req is None, repr(add_req)
        if isinstance(ref, NamedRef):
            return ref_to_req(types, ref.backref, Node([Field(ref.name)]))
        else:
            return ref_to_req(types, ref.backref)

    else:
        raise TypeError("Is not one of hiku.types: {!r}".format(ref_type))


def type_to_query(type_):
    if isinstance(type_, RecordMeta):
        assert isinstance(type_, RecordMeta), type(type_)
        fields = []
        for f_name, f_type in type_.__field_types__.items():
            f_query = type_to_query(f_type)
            if f_query is not None:
                fields.append(Link(f_name, f_query))
            else:
                fields.append(Field(f_name))
        return Node(fields)
    elif isinstance(type_, SequenceMeta):
        return type_to_query(type_.__item_type__)
    elif isinstance(type_, OptionalMeta):
        return type_to_query(type_.__type__)
    else:
        return None


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
        ref = getattr(node, "__ref__", None)
        if ref is not None:
            req = ref_to_req(self._types, ref)
            if req is not None:
                self._reqs.append(req)
        super(RequirementsExtractor, self).visit(node)

    def visit_tuple(self, node):
        sym, args = node.values[0], node.values[1:]
        sym_ref = getattr(sym, "__ref__", None)
        if sym_ref is not None:
            for arg, arg_type in zip(args, sym_ref.to.__arg_types__):
                arg_query = type_to_query(arg_type)
                if arg_query is not None:
                    self._reqs.append(
                        ref_to_req(self._types, arg.__ref__, arg_query)
                    )
                else:
                    self.visit(arg)
        else:
            for arg in args:
                self.visit(arg)
