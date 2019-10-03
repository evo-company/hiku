from collections import deque

from ..query import QueryVisitor, Link, Field
from ..types import TypeRefMeta, OptionalMeta, SequenceMeta, get_type


class Denormalize(QueryVisitor):

    def __init__(self, graph, result):
        self._types = graph.__types__
        self._result = result
        self._type = deque([self._types['__root__']])
        self._data = deque([result])
        self._res = deque()

    def process(self, query):
        assert not self._res, self._res
        self._res.append({})
        self.visit(query)
        return self._res.pop()

    def visit_field(self, obj: Field):
        self._res[-1][obj.result_key] = self._data[-1][obj.result_key]

    def visit_link(self, obj: Link):
        type_ = self._type[-1].__field_types__[obj.name]
        if isinstance(type_, TypeRefMeta):
            self._type.append(get_type(self._types, type_))
            self._res.append({})
            self._data.append(self._data[-1][obj.result_key])
            super().visit_link(obj)
            self._data.pop()
            self._res[-1][obj.result_key] = self._res.pop()
            self._type.pop()
        elif isinstance(type_, SequenceMeta):
            self._type.append(get_type(self._types, type_.__item_type__))
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
                self._type.append(get_type(self._types, type_.__type__))
                self._res.append({})
                self._data.append(self._data[-1][obj.result_key])
                super().visit_link(obj)
                self._data.pop()
                self._res[-1][obj.result_key] = self._res.pop()
                self._type.pop()
        else:
            raise AssertionError(repr(type_))
