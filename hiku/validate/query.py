import typing as t

from contextlib import contextmanager
from collections import abc as collections_abc

from hiku.scalar import ScalarMeta

from ..types import (
    AbstractTypeVisitor,
    IDMeta,
    Record,
    OptionalMeta,
    SequenceMeta,
    RecordMeta,
    TypeRefMeta,
    GenericMeta,
    AnyMeta,
    BooleanMeta,
    StringMeta,
    IntegerMeta,
    FloatMeta,
    MappingMeta,
)

from hiku.query import (
    Field as QueryField,
    FieldBase,
    Fragment,
    Node as QueryNode,
    Link as QueryLink,
    QueryVisitor,
)
from hiku.graph import (
    Interface,
    LinkType,
    Node,
    Field,
    Link,
    GraphVisitor,
    Root,
    Option,
    Nothing,
    Graph,
    Union,
)
from .errors import Errors


_undefined = object()


OptionValue = t.Union[
    int, str, float, bool, collections_abc.Sequence, collections_abc.Mapping
]


class _AssumeRecord(AbstractTypeVisitor):
    def __init__(
        self, data_types: t.Dict[str, t.Type[Record]], _nested: bool = False
    ):
        self._data_types = data_types
        self._nested = _nested

    def _get_nested(self) -> "_AssumeRecord":
        return _AssumeRecord(self._data_types, _nested=True)

    def visit(self, obj: t.Any) -> t.Any:
        if obj is not None:
            return obj.accept(self)

    def _false(self, obj: t.Any) -> None:
        pass

    visit_any = _false
    visit_boolean = _false
    visit_string = _false
    visit_id = _false
    visit_integer = _false
    visit_float = _false
    visit_mapping = _false
    visit_callable = _false
    visit_unionref = _false
    visit_interfaceref = _false
    visit_enumref = _false
    visit_scalar = _false

    def visit_optional(self, obj: OptionalMeta) -> t.Optional[t.OrderedDict]:
        if not self._nested:
            return self._get_nested().visit(obj.__type__)
        return None

    def visit_sequence(self, obj: SequenceMeta) -> t.Optional[t.OrderedDict]:
        if not self._nested:
            return self._get_nested().visit(obj.__item_type__)
        return None

    def visit_record(self, obj: RecordMeta) -> t.OrderedDict:
        # return fields alongside type definitions
        return obj.__field_types__

    def visit_typeref(self, obj: TypeRefMeta) -> t.OrderedDict:
        return self.visit(self._data_types[obj.__type_name__])


class _AssumeField(GraphVisitor):
    def __init__(self, node: Node, errors: Errors) -> None:
        self.node = node
        self.errors = errors

    def visit_field(self, obj: Field) -> bool:
        return True

    def visit_link(self, obj: Link) -> bool:
        self.errors.report(
            'Trying to query "{}.{}" link as it was a field'.format(
                self.node.name or "root", obj.name
            )
        )
        return False

    def visit_node(self, obj: Node) -> bool:
        assert (
            self.node.name is None
        ), "Nested node can be only in the root node"
        self.errors.report(
            'Trying to query "{}" node as it was a field'.format(obj.name)
        )
        return False

    def visit_root(self, obj: Root) -> t.NoReturn:
        raise AssertionError("Root node is not expected here")


class _OptionError(TypeError):
    def __init__(self, description: str) -> None:
        self.description = description
        super(_OptionError, self).__init__(description)


class _OptionTypeError(_OptionError):
    def __init__(self, value: OptionValue, expected: GenericMeta) -> None:
        description = '"{}" instead of {!r}'.format(
            type(value).__name__, expected
        )
        super(_OptionTypeError, self).__init__(description)


class _OptionTypeValidator:
    def __init__(
        self, data_types: t.Dict[str, t.Type[Record]], value: OptionValue
    ) -> None:
        self._data_types = data_types
        self._value = [value]

    @property
    def value(self) -> OptionValue:
        return self._value[-1]

    @contextmanager
    def push(self, value: OptionValue) -> t.Iterator[None]:
        self._value.append(value)
        try:
            yield
        finally:
            self._value.pop()

    def visit(self, type_: GenericMeta) -> None:
        type_.accept(self)  # type: ignore

    def visit_any(self, type_: AnyMeta) -> None:
        pass

    def visit_boolean(self, type_: BooleanMeta) -> None:
        if not isinstance(self.value, bool):
            raise _OptionTypeError(self.value, type_)
        return None

    def visit_string(self, type_: StringMeta) -> None:
        if not isinstance(self.value, str):
            raise _OptionTypeError(self.value, type_)
        return None

    def visit_id(self, type_: IDMeta) -> None:
        if not isinstance(self.value, str):
            raise _OptionTypeError(self.value, type_)
        return None

    def visit_integer(self, type_: IntegerMeta) -> None:
        if not isinstance(self.value, int):
            raise _OptionTypeError(self.value, type_)
        return None

    def visit_float(self, type_: FloatMeta) -> None:
        if not isinstance(self.value, float):
            raise _OptionTypeError(self.value, type_)
        return None

    def visit_optional(self, type_: OptionalMeta) -> None:
        if self.value is not None:
            self.visit(type_.__type__)
        return None

    def visit_sequence(self, type_: SequenceMeta) -> None:
        if not isinstance(self.value, collections_abc.Sequence):
            raise _OptionTypeError(self.value, type_)
        for item in self.value:
            with self.push(item):
                self.visit(type_.__item_type__)

        return None

    def visit_mapping(self, type_: MappingMeta) -> None:
        if not isinstance(self.value, collections_abc.Mapping):
            raise _OptionTypeError(self.value, type_)
        for key, value in self.value.items():
            with self.push(key):
                self.visit(type_.__key_type__)
            with self.push(value):
                self.visit(type_.__value_type__)

        return None

    def visit_record(self, type_: RecordMeta) -> None:
        if not isinstance(self.value, collections_abc.Mapping):
            raise _OptionTypeError(self.value, type_)

        unknown = set(self.value).difference(type_.__field_types__)
        if unknown:
            fields = ", ".join(sorted(map(repr, unknown)))
            raise _OptionError("unknown fields: {}".format(fields))

        missing = set(type_.__field_types__).difference(self.value)
        if missing:
            fields = ", ".join(sorted(missing))
            raise _OptionError("missing fields: {}".format(fields))

        for key, value_type in type_.__field_types__.items():
            with self.push(self.value[key]):
                self.visit(value_type)

        return None

    def visit_typeref(self, type_: TypeRefMeta) -> None:
        assert (
            type_.__type_name__ in self._data_types
        ), f'"{type_.__type_name__}" type is not present in graph data_types'
        self.visit(self._data_types[type_.__type_name__])

    # TODO: add scalar validation errors
    def visit_scalar(self, type_: ScalarMeta) -> None:
        pass


class _ValidateOptions(GraphVisitor):
    """
    Validate options for fields and links.

    :param data_types: Mapping of data types.
    :param options: Options to validate.
    :param for_: Path to the field or link. Used in error messages.
    :param errors: Errors container.
    """

    def __init__(
        self,
        data_types: t.Dict[str, t.Type[Record]],
        options: t.Optional[t.Dict],
        for_: t.Tuple[t.Any, ...],
        errors: Errors,
    ) -> None:
        self._data_types = data_types
        self.options = options
        self.for_ = for_
        self.errors = errors
        self._options = options or {}

    def visit_link(self, obj: Link) -> None:
        super(_ValidateOptions, self).visit_link(obj)
        unknown = set(self._options).difference(obj.options_map)
        if unknown:
            node, field = self.for_
            self.errors.report(
                'Unknown options for "{}.{}": {}'.format(
                    node, field, ", ".join(unknown)
                )
            )

        return None

    visit_field = visit_link  # type: ignore

    def visit_option(self, obj: Option) -> None:
        value = self._options.get(obj.name, obj.default)
        if value is Nothing:
            node, field = self.for_
            self.errors.report(
                'Required option "{}.{}:{}" is not specified'.format(
                    node, field, obj.name
                )
            )
        elif obj.type is not None:
            try:
                _OptionTypeValidator(self._data_types, value).visit(obj.type)
            except _OptionError as err:
                node, field = self.for_
                self.errors.report(
                    'Invalid value for option "{}.{}:{}", {}'.format(
                        node, field, obj.name, err.description
                    )
                )

        return None

    def visit_node(self, obj: Node) -> None:
        assert self.options is None, "Node can not have options"

    def visit_root(self, obj: Root) -> t.NoReturn:
        raise AssertionError("Root node is not expected here")


class _RecordFieldsValidator(QueryVisitor):
    def __init__(
        self,
        data_types: t.Dict[str, t.Type[Record]],
        field_types: t.OrderedDict,
        errors: Errors,
    ) -> None:
        self._data_types = data_types
        self._field_types = field_types
        self._errors = errors

    def visit_field(self, obj: QueryField) -> None:
        if obj.name == "__typename":
            return

        if obj.name not in self._field_types:
            self._errors.report('Unknown field name "{}"'.format(obj.name))
        elif obj.options is not None:
            self._errors.report("Options are not expected")
        elif _AssumeRecord(self._data_types).visit(self._field_types[obj.name]):
            self._errors.report(
                'Trying to query "{}" link as it was a field'.format(obj.name)
            )

    def visit_link(self, obj: QueryLink) -> None:
        field_types = _AssumeRecord(self._data_types).visit(
            self._field_types[obj.name]
        )
        if field_types is not None:
            fields_validator = _RecordFieldsValidator(
                self._data_types, field_types, self._errors
            )
            for field in obj.node.fields:
                fields_validator.visit(field)
        else:
            self._errors.report('"{}" is not a link'.format(obj.name))

    def visit_node(self, obj: QueryNode) -> None:
        raise AssertionError("Node is not expected here")


def _field_eq(a: FieldBase, b: FieldBase) -> bool:
    return a.name == b.name and a.options == b.options


class DefaultQueryValidator(QueryVisitor):
    """
    Validate query against graph.

    Query must not contain __typename field.

    :param graph: Graph to validate against.
    """

    def __init__(self, graph: Graph):
        self.graph = graph
        self.path = [graph.root]
        self.errors = Errors()

    def visit_field(self, obj: QueryField) -> None:
        node = self.path[-1]
        field = node.fields_map.get(obj.name)
        if field is not None:
            is_field = _AssumeField(node, self.errors).visit(field)
            if is_field:
                for_ = (node.name or "root", obj.name)
                _ValidateOptions(
                    self.graph.data_types, obj.options, for_, self.errors
                ).visit(field)
        else:
            self.errors.report(
                'Field "{}" is not implemented in the "{}" node'.format(
                    obj.name, node.name or "root"
                )
            )

    def visit_link(self, obj: QueryLink) -> None:
        node = self.path[-1]
        graph_obj = node.fields_map.get(obj.name, _undefined)
        if isinstance(graph_obj, Field):
            for_ = (node.name or "root", obj.name)
            _ValidateOptions(
                self.graph.data_types, obj.options, for_, self.errors
            ).visit(graph_obj)

            field_types = _AssumeRecord(self.graph.data_types).visit(
                graph_obj.type
            )
            if field_types is not None:
                fields_validator = _RecordFieldsValidator(
                    self.graph.data_types, field_types, self.errors
                )
                for field in obj.node.fields:
                    fields_validator.visit(field)
            else:
                self.errors.report(
                    'Trying to query "{}.{}" simple field '
                    "as node".format(node.name or "root", obj.name)
                )

        elif isinstance(graph_obj, Link):
            if graph_obj.type_info.type_enum is LinkType.UNION:
                linked_node = self.graph.unions_map[graph_obj.node]
            elif graph_obj.type_info.type_enum is LinkType.INTERFACE:
                linked_node = self.graph.interfaces_map[graph_obj.node]
            else:
                linked_node = self.graph.nodes_map[graph_obj.node]

            for_ = (node.name or "root", obj.name)
            _ValidateOptions(
                self.graph.data_types, obj.options, for_, self.errors
            ).visit(graph_obj)

            self.path.append(linked_node)
            try:
                self.visit(obj.node)
            finally:
                self.path.pop()

        elif graph_obj is _undefined:
            self.errors.report(
                'Link "{}" is not implemented in the "{}" node'.format(
                    obj.name, node.name or "root"
                )
            )
        else:
            raise TypeError(repr(graph_obj))

    def visit_fragment(self, obj: Fragment) -> t.Any:
        graph_node = self.graph.nodes_map[obj.type_name]
        self.path.append(graph_node)
        for field in obj.node.fields:
            if field.name == "__typename":
                continue
            self.visit(field)

        self.path.pop()

    def visit_node(self, obj: QueryNode) -> None:
        fields: t.Dict = {}

        is_union_link = isinstance(self.path[-1], Union)
        is_interface_link = isinstance(self.path[-1], Interface)

        for field in obj.fields:
            if field.name == "__typename":
                continue

            if is_union_link:
                union = self.path[-1]
                if not isinstance(field, Fragment):
                    self.errors.report(
                        "Cannot query field '{}' on type '{}'. "
                        "Did you mean to use an inline fragment on {}?".format(
                            field.name,
                            union.name,
                            " or ".join(
                                [f"'{type_name}'" for type_name in union.types]
                            ),
                        )
                    )
                    continue

                self.visit(field)
                continue
            elif is_interface_link:
                if isinstance(field, Fragment):
                    self.visit(field)
                    continue

                interface = self.path[-1]

                interface_types = self.graph.interfaces_types[interface.name]
                if not interface_types:
                    self.errors.report(
                        "Can not query field '{0}' on interface '{1}'. "
                        "Interface '{1}' is not implemented by any type. "
                        "Add at least one type implementing this interface.".format(  # noqa: E501
                            field.name, interface.name
                        )
                    )
                    continue

                if field.name not in interface.fields_map:
                    implementation = None
                    for impl in interface_types:
                        if field.name in self.graph.nodes_map[impl].fields_map:
                            implementation = impl
                            break

                    self.errors.report(
                        "Can not query field '{}' on type '{}'. "
                        "Did you mean to use an inline fragment on '{}'?".format(  # noqa: E501
                            field.name, interface.name, implementation
                        )
                    )
                    continue

            seen = fields.get(field.result_key)
            if seen is not None:
                if not _field_eq(field, seen):
                    node = self.path[-1].name or "root"
                    self.errors.report(
                        "Found distinct fields with the same "
                        'resulting name "{}" for the node "{}"'.format(
                            field.result_key, node
                        )
                    )
            else:
                fields[field.result_key] = field
            self.visit(field)

            if is_union_link:
                self.path.pop()

        for fr in obj.fragments:
            self.visit(fr)


def validate(graph: Graph, query: QueryNode) -> t.List[str]:
    query_validator = DefaultQueryValidator(graph)
    query_validator.visit(query)
    return query_validator.errors.list
