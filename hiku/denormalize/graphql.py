from collections import deque

from ..graph import Graph, Union
from ..query import Field, Link
from ..result import Proxy
from ..types import (
    RecordMeta,
    TypeRefMeta,
    SequenceMeta,
    OptionalMeta,
    GenericMeta,
    UnionRefMeta,
)

from .base import Denormalize


class DenormalizeGraphQL(Denormalize):
    def __init__(
        self, graph: Graph, result: Proxy, root_type_name: str
    ) -> None:
        super().__init__(graph, result)
        self._type_name = deque([root_type_name])

    def visit_field(self, obj: Field) -> None:
        if obj.name == "__typename":
            type_name = self._type_name[-1]
            if isinstance(self._type[-1], Union):
                type_name = self._data[-1].__ref__.node
            self._res[-1][obj.result_key] = type_name
        else:
            if isinstance(self._type[-1], Union):
                type_name = self._data[-1].__ref__.node

                if obj.name not in self._types[type_name].__field_types__:
                    return
            super().visit_field(obj)

    def visit_link(self, obj: Link) -> None:
        if isinstance(self._type[-1], Union):
            assert obj.parent_type in self._type[-1].types
            type_ = self._types[obj.parent_type].__field_types__[obj.name]
        elif isinstance(self._type[-1], RecordMeta):
            type_ = self._type[-1].__field_types__[obj.name]
        else:
            raise AssertionError(repr(self._type[-1]))

        type_ref: GenericMeta
        if isinstance(type_, (TypeRefMeta, UnionRefMeta)):
            type_ref = type_
        elif isinstance(type_, SequenceMeta):
            type_ref = type_.__item_type__
            if isinstance(type_ref, OptionalMeta):
                type_ref = type_ref.__type__
            assert isinstance(type_ref, (TypeRefMeta, UnionRefMeta)), type_ref
        elif isinstance(type_, OptionalMeta):
            type_ref = type_.__type__
            assert isinstance(type_ref, (TypeRefMeta, UnionRefMeta)), type_ref
        else:
            raise AssertionError(repr(type_))
        self._type_name.append(type_ref.__type_name__)
        super().visit_link(obj)
        self._type_name.pop()
