from collections import deque

from ..query import Field, Link
from ..types import TypeRefMeta, SequenceMeta, OptionalMeta

from .base import Denormalize


class DenormalizeGraphQL(Denormalize):

    def __init__(self, graph, result, root_type_name):
        super().__init__(graph, result)
        self._type_name = deque([root_type_name])

    def visit_field(self, obj: Field):
        if obj.name == '__typename':
            self._res[-1][obj.result_key] = self._type_name[-1]
        else:
            super().visit_field(obj)

    def visit_link(self, obj: Link):
        type_ = self._type[-1].__field_types__[obj.name]
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
