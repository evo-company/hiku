from collections import deque

from ..graph import Graph, Interface, Union
from ..query import Field, Link
from ..result import Proxy
from ..types import (
    RecordMeta,
    RefMeta,
    SequenceMeta,
    OptionalMeta,
    GenericMeta,
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
            if isinstance(self._type[-1], (Union, Interface)):
                type_name = self._data[-1].__ref__.node
            self._res[-1][obj.result_key] = type_name
        else:
            super().visit_field(obj)

    def visit_link(self, obj: Link) -> None:
        if isinstance(self._type[-1], (Union, Interface)):
            type_ = self._types[self._data[-1].__ref__.node].__field_types__[
                obj.name
            ]
        elif isinstance(self._type[-1], RecordMeta):
            type_ = self._type[-1].__field_types__[obj.name]
        else:
            raise AssertionError(repr(self._type[-1]))

        type_ref: GenericMeta
        if isinstance(type_, RefMeta):
            type_ref = type_
        elif isinstance(type_, SequenceMeta):
            type_ref = type_.__item_type__
            if isinstance(type_ref, OptionalMeta):
                type_ref = type_ref.__type__
            assert isinstance(type_ref, RefMeta), type_ref
        elif isinstance(type_, OptionalMeta):
            type_ref = type_.__type__
            assert isinstance(type_ref, RefMeta), type_ref
        else:
            raise AssertionError(repr(type_))
        self._type_name.append(type_ref.__type_name__)
        super().visit_link(obj)
        self._type_name.pop()
