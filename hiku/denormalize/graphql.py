from collections import deque

from ..graph import Graph
from ..query import Field, Link
from ..result import Proxy
from ..types import (
    TypeRefMeta,
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
            self._res[-1][obj.result_key] = self._type_name[-1]
        else:
            super().visit_field(obj)

    def visit_link(self, obj: Link) -> None:
        type_ = self._type[-1].__field_types__[obj.name]
        type_ref: GenericMeta
        if isinstance(type_, TypeRefMeta):
            type_ref = type_
        elif isinstance(type_, SequenceMeta):
            type_ref = type_.__item_type__
            assert isinstance(type_ref, TypeRefMeta), type_ref
        elif isinstance(type_, OptionalMeta):
            type_ref = type_.__type__
            assert isinstance(type_ref, TypeRefMeta), type_ref
        else:
            raise AssertionError(repr(type_))
        self._type_name.append(type_ref.__type_name__)
        super().visit_link(obj)
        self._type_name.pop()
