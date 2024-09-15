import typing as t
from typing import Protocol

from itertools import chain
from contextlib import contextmanager
from collections import Counter

from ..directives import Deprecated
from ..enum import BaseEnum
from ..graph import (
    FieldType,
    GraphVisitor,
    Interface,
    Root,
    Field,
    Node,
    Link,
    Option,
    Graph,
    Union,
)
from ..graph import AbstractNode, AbstractField, AbstractLink, AbstractOption

from .errors import Errors
from ..scalar import Scalar
from ..types import GenericMeta, OptionalMeta


class DescriptionProtocol(Protocol):
    description: t.Optional[str]


class GraphValidationError(TypeError):
    def __init__(self, errors: t.List[str]) -> None:
        self.errors = errors
        errors_list = "\n".join("- {}".format(e) for e in errors)
        super(GraphValidationError, self).__init__("\n" + errors_list)


class GraphValidator(GraphVisitor):
    class _NameFormatter(GraphVisitor):
        def visit_node(self, obj: Node) -> t.Optional[str]:
            return obj.name

        def visit_root(self, obj: Root) -> str:
            return "root"

        def visit_link(self, obj: Link) -> str:
            return ".{}".format(obj.name)

        def visit_field(self, obj: Field) -> str:
            return ".{}".format(obj.name)

        def visit_option(self, obj: Option) -> str:
            return ":{}".format(obj.name)

        def visit_scalar(self, obj: t.Type[Scalar]) -> str:
            return obj.__type_name__

    _name_formatter = _NameFormatter()
    _graph_accept_types = (AbstractNode,)
    _node_accept_types = (AbstractField, AbstractLink)
    _link_accept_types = (AbstractOption,)
    _field_accept_types = (AbstractOption,)

    def __init__(
        self,
        items: t.List[Node],
        unions: t.List[Union],
        interfaces: t.List[Interface],
        enums: t.List[BaseEnum],
        scalars: t.List[t.Type[Scalar]],
    ) -> None:
        self.items = items
        self.unions = unions
        self.unions_map = {u.name: u for u in unions}
        self.interfaces = interfaces
        self.interfaces_map = {i.name: i for i in interfaces}
        self.enums = enums
        self.scalars = scalars
        self.scalars_map = {s.__type_name__: s for s in scalars}
        self.errors = Errors()
        self._ctx: t.List = []

    @classmethod
    def validate(
        cls,
        items: t.List[Node],
        unions: t.List[Union],
        interfaces: t.List[Interface],
        enums: t.List[BaseEnum],
        scalars: t.List[t.Type[Scalar]],
    ) -> None:
        validator = cls(items, unions, interfaces, enums, scalars)
        validator.visit_graph_items(items)
        validator.visit_graph_unions(unions)
        validator.visit_graph_interfaces(interfaces)
        validator.visit_graph_enums(enums)
        validator.visit_graph_scalars(scalars)
        if validator.errors.list:
            raise GraphValidationError(validator.errors.list)

    @contextmanager
    def push_ctx(self, obj: t.Union[Node, Link, Field]) -> t.Any:
        self._ctx.append(obj)
        try:
            yield
        finally:
            self._ctx.pop()

    @property
    def ctx(self) -> t.Union[Node, Link, Field]:
        return self._ctx[-1]

    def _get_duplicates(self, names: t.Iterable[str]) -> t.List[str]:
        counter = Counter(names)
        return [k for k, v in counter.items() if v > 1]

    def _format_names(self, names: t.List[str]) -> str:
        return ", ".join('"{}"'.format(name) for name in names)

    def _format_types(self, objects: t.List[t.Any]) -> str:
        return ", ".join(map(repr, set(type(obj) for obj in objects)))

    def _format_path(self, obj: t.Optional[t.Any] = None) -> str:
        path = self._ctx + ([obj] if obj is not None else [])
        return "".join(self._name_formatter.visit(i) for i in path)

    def _validate_deprecated_duplicates(
        self, obj: t.Union[Field, Link]
    ) -> None:
        deprecated_count = sum(
            (1 for d in obj.directives if isinstance(d, Deprecated))
        )
        if deprecated_count > 1:
            self.errors.report(
                'Deprecated directive must be used only once for "{}", found {}'.format(  # noqa: E501
                    self._format_path(obj), deprecated_count
                )
            )

    def _validate_description(self, obj: DescriptionProtocol) -> None:
        if obj.description is not None:
            if not isinstance(obj.description, str):
                self.errors.report(
                    '{} "{}" description must be a string'.format(
                        obj.__class__.__name__, self._format_path(obj)
                    ),
                )

    def visit_option(self, obj: Option) -> None:
        if (
            isinstance(obj.type, GenericMeta)
            and not isinstance(obj.type, OptionalMeta)
            and obj.default is None
        ):
            self.errors.report(
                'Non-optional option "{}" must have a default value'.format(
                    self._format_path(obj)
                ),
            )

        self._validate_description(obj)

    def visit_field(self, obj: Field) -> None:
        invalid = [
            f
            for f in obj.options
            if not isinstance(f, self._field_accept_types)
        ]
        if invalid:
            self.errors.report(
                'Invalid types provided as field "{}" options: {}'.format(
                    self._format_path(obj), self._format_types(invalid)
                )
            )
            return

        with self.push_ctx(obj):
            super(GraphValidator, self).visit_field(obj)

        if obj.type_info and obj.type_info.type_enum is FieldType.CUSTOM_SCALAR:
            if obj.type_info.type_name not in self.scalars_map:
                self.errors.report(
                    'Field "{}" has type "{!r}" but no scalar is '
                    "defined for it. "
                    "Maybe you forgot to add new scalar to Graph(..., scalars)?".format(  # noqa: E501
                        self._format_path(obj), obj.type
                    )
                )
                return

        if (
            obj.type is not None
            and not isinstance(obj.type, GenericMeta)
            and not obj.type_info
        ):
            self.errors.report(
                'Field "{}" has type "{!r}" but Hiku does not support it.'.format(  # noqa: E501
                    self._format_path(obj), obj.type
                )
            )
            return

        self._validate_description(obj)
        self._validate_deprecated_duplicates(obj)

    def visit_link(self, obj: Link) -> None:
        assert isinstance(self.ctx, Node)

        invalid = [
            f for f in obj.options if not isinstance(f, self._link_accept_types)
        ]
        if invalid:
            self.errors.report(
                'Invalid types provided as link "{}" options: {}'.format(
                    self._format_path(obj), self._format_types(invalid)
                )
            )
            return

        with self.push_ctx(obj):
            super(GraphValidator, self).visit_link(obj)

        graph_nodes = {e.name for e in self.items if e.name is not None}
        if obj.node not in (
            graph_nodes | self.unions_map.keys() | self.interfaces_map.keys()
        ):
            self.errors.report(
                'Link "{}" points to the missing node "{}"'.format(
                    self._format_path(obj), obj.node
                )
            )

        if obj.requires is not None:
            requires = (
                obj.requires
                if isinstance(obj.requires, list)
                else [obj.requires]
            )

            for r in requires:
                if r not in self.ctx.fields_map:
                    self.errors.report(
                        'Link "{}" requires missing field "{}" in the "{}" node'.format(  # noqa: E501
                            obj.name, r, self._format_path()
                        )
                    )

        self._validate_description(obj)
        self._validate_deprecated_duplicates(obj)

    def visit_node(self, obj: Node) -> None:
        node_name = obj.name or "root"
        invalid = [
            f for f in obj.fields if not isinstance(f, self._node_accept_types)
        ]
        if invalid:
            self.errors.report(
                'Node can not contain these types: {} in node "{}"'.format(
                    self._format_types(invalid), node_name
                )
            )
            return

        with self.push_ctx(obj):
            for item in obj.fields:
                self.visit(item)

        duplicates = self._get_duplicates(e.name for e in obj.fields)
        if duplicates:
            self.errors.report(
                'Duplicated names found in the "{}" node: {}'.format(
                    node_name, self._format_names(duplicates)
                )
            )

        if sum((1 for d in obj.directives if isinstance(d, Deprecated))) > 0:
            self.errors.report("Deprecated directive can not be used in Node")

        if obj.implements:
            for i in obj.implements:
                if i not in self.interfaces_map:
                    self.errors.report(
                        'Node "{}" implements missing interface "{}"'.format(
                            node_name, i
                        )
                    )

        self._validate_description(obj)

    def visit_union(self, obj: "Union") -> t.Any:
        if not obj.name:
            self.errors.report("Union must have a name")

        if not obj.types:
            self.errors.report("Union must have at least one type")

        nodes_map = {e.name: e for e in self.items if e.name is not None}

        invalid = [type_ for type_ in obj.types if type_ not in nodes_map]

        if invalid:
            self.errors.report(
                "Union '{}' types '{}' must point to node or data type".format(
                    obj.name, invalid
                )
            )
            return

        self._validate_description(obj)

    def visit_interface(self, obj: "Interface") -> t.Any:
        if not obj.name:
            self.errors.report("Interface must have a name")

        if not obj.fields:
            self.errors.report(
                "Interface '{}' must have at least one field".format(obj.name)
            )

        invalid = [
            type_
            for type_ in obj.fields
            if not isinstance(type_, (Field, Link))
        ]

        if invalid:
            self.errors.report(
                "Interface '{}' fields must be of type 'Field', found '{}'".format(  # noqa: E501
                    obj.name, invalid
                )
            )
            return

        self._validate_description(obj)

    def visit_enum(self, obj: BaseEnum) -> t.Any:
        if not obj.name:
            self.errors.report("Enum must have a name")
            return

        if not obj.values:
            self.errors.report("Enum must have at least one value")
            return

        self._validate_description(obj)

    def visit_scalar(self, obj: t.Type[Scalar]) -> t.Any: ...

    def visit_root(self, obj: Root) -> None:
        self.visit_node(obj)

    def visit_graph(self, obj: Graph) -> None:
        self.visit_graph_items(obj.items)

    def visit_graph_items(self, items: t.List[Node]) -> None:
        invalid = [
            f for f in items if not isinstance(f, self._graph_accept_types)
        ]
        if invalid:
            self.errors.report(
                "Graph can not contain these types: {}".format(
                    self._format_types(invalid)
                )
            )
            return

        root = Root(
            list(chain.from_iterable(e.fields for e in items if e.name is None))
        )
        self.visit(root)

        for item in items:
            if item.name is not None:
                self.visit(item)

        duplicates = self._get_duplicates(
            e.name for e in items if e.name is not None
        )
        if duplicates:
            self.errors.report(
                "Duplicated nodes found in the graph: {}".format(
                    self._format_names(duplicates)
                )
            )

    def visit_graph_unions(self, unions: t.List[Union]) -> None:
        for union in unions:
            self.visit(union)

    def visit_graph_interfaces(self, interfaces: t.List[Interface]) -> None:
        for interface in interfaces:
            self.visit(interface)

    def visit_graph_enums(self, enums: t.List[BaseEnum]) -> None:
        for enum in enums:
            self.visit(enum)

    def visit_graph_scalars(self, scalars: t.List[t.Type[Scalar]]) -> None:
        for scalar in scalars:
            self.visit(scalar)
