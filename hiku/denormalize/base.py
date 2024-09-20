import typing as t
from collections import deque

from ..enum import BaseEnum
from ..graph import (
    FieldType,
    Graph,
    Interface,
    Union,
    Field as GraphField,
)
from ..query import (
    Fragment,
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
from ..utils.serialize import serialize


def serialize_value(graph: Graph, field: GraphField, value: t.Any) -> t.Any:
    """Serializes value according to the field type."""
    if not field.type_info:
        return value

    field_type = field.type_info.type_enum
    type_name = field.type_info.type_name

    if field_type in (FieldType.SCALAR, FieldType.RECORD):
        return value
    elif field_type is FieldType.ENUM:
        enum = graph.enums_map[type_name]
        return serialize(field.type, value, enum.serialize)
    elif field_type is FieldType.CUSTOM_SCALAR:
        scalar = graph.scalars_map[type_name]
        return serialize(field.type, value, scalar.serialize)
    else:
        raise TypeError(
            'Unknown field "{}" type "{!r}"'.format(field.name, field.type)
        )


class Denormalize(QueryVisitor):
    def __init__(self, graph: Graph, result: Proxy) -> None:
        self._graph = graph
        self._types = graph.__types__
        self._unions = graph.unions_map
        self._enums = graph.enums_map
        self._result = result
        self._index = result.__idx__
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

    def visit_node(self, obj: Node) -> t.Any:
        for item in obj.fields:
            self.visit(item)

        for i, fr in enumerate(obj.fragments):
            self.visit_fragment(fr, i)

    def visit_fragment(self, obj: Fragment, idx: int) -> None:  # type: ignore[override]  # noqa: E501
        type_name = None
        if isinstance(self._data[-1], Proxy):
            type_name = self._data[-1].__ref__.node

        if type_name is not None and type_name != obj.type_name:
            # for unions we must visit only fragments with same type as node
            return

        if isinstance(self._data[-1], Proxy):
            node = self._data[-1].__node__.fragments[idx].node
            ref = self._data[-1].__ref__
            self._data.append(Proxy(self._index, ref, node))
        else:
            self._data.append(self._data[-1])
        for item in obj.node.fields:
            self.visit(item)
        self._data.pop()

    def visit_field(self, obj: Field) -> None:
        if isinstance(self._data[-1], Proxy):
            type_name = self._data[-1].__ref__.node
            if type_name == "__root__":
                node = self._graph.root
            else:
                node = self._graph.nodes_map[type_name]
            graph_field = node.fields_map[obj.name]

            self._res[-1][obj.result_key] = serialize_value(
                self._graph, graph_field, self._data[-1][obj.result_key]
            )
        else:
            # Record type itself does not have custom serialization
            # TODO: support Scalar/Enum types in Record

            # if record field is aliased, use index_key as a result-key
            result_key = obj.result_key if obj.alias is None else obj.index_key
            self._res[-1][obj.result_key] = self._data[-1][result_key]

    def visit_link(self, obj: Link) -> None:
        if isinstance(self._type[-1], (Union, Interface)):
            type_ = self._types[self._data[-1].__ref__.node].__field_types__[
                obj.name
            ]
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
