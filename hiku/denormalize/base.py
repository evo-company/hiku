import typing as t
from collections import deque

from ..enum import BaseEnum
from ..graph import Graph, Interface, Union
from ..query import (
    QueryVisitor,
    Link,
    Field,
    Node,
)
from ..result import Proxy
from ..types import (
    Record,
    RecordMeta,
    RefMeta,
    OptionalMeta,
    SequenceMeta,
    get_type,
)


class Denormalize(QueryVisitor):
    def __init__(self, graph: Graph, result: Proxy) -> None:
        self._types = graph.__types__
        self._unions = graph.unions_map
        self._result = result
        self._type: t.Deque[
            t.Union[t.Type[Record], Union, Interface, BaseEnum]
        ] = deque([self._types["__root__"]])
        self._data = deque([result])
        self._res: t.Deque = deque()

    def process(self, query: Node) -> t.Dict:
        assert not self._res, self._res
        self._res.append({})
        self.visit(query)
        return self._res.pop()

    def visit_field(self, obj: Field) -> None:
        self._res[-1][obj.result_key] = self._data[-1][obj.result_key]

    def visit_link(self, obj: Link) -> None:
        if isinstance(self._type[-1], Union):
            assert obj.parent_type in self._type[-1].types
            type_ = self._types[obj.parent_type].__field_types__[obj.name]
        elif isinstance(self._type[-1], RecordMeta):
            type_ = self._type[-1].__field_types__[obj.name]
        else:
            raise AssertionError(repr(self._type[-1]))

        if isinstance(type_, RefMeta):
            self._type.append(get_type(self._types, type_))
            self._res.append({})
            self._data.append(self._data[-1][obj.result_key])
            super().visit_link(obj)
            self._data.pop()
            self._res[-1][obj.result_key] = self._res.pop()
            self._type.pop()
        elif isinstance(type_, SequenceMeta):
            type_ref = type_.__item_type__
            if isinstance(type_.__item_type__, OptionalMeta):
                type_ref = type_.__item_type__.__type__
            assert isinstance(type_ref, RefMeta)
            self._type.append(get_type(self._types, type_ref))
            items = []
            for item in self._data[-1][obj.result_key]:
                self._res.append({})
                self._data.append(item)
                super().visit_link(obj)
                self._data.pop()
                items.append(self._res.pop())
            self._res[-1][obj.result_key] = items
            self._type.pop()
        elif isinstance(type_, OptionalMeta):
            if self._data[-1][obj.result_key] is None:
                self._res[-1][obj.result_key] = None
            else:
                assert isinstance(type_.__type__, RefMeta)
                self._type.append(get_type(self._types, type_.__type__))
                self._res.append({})
                self._data.append(self._data[-1][obj.result_key])
                super().visit_link(obj)
                self._data.pop()
                self._res[-1][obj.result_key] = self._res.pop()
                self._type.pop()
        else:
            raise AssertionError(repr(type_))
