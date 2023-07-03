import typing as t

from itertools import chain
from contextlib import contextmanager
from collections import Counter

from ..directives import Deprecated
from ..graph import (
    GraphVisitor,
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
from ..types import GenericMeta, OptionalMeta


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

    _name_formatter = _NameFormatter()
    _graph_accept_types = (AbstractNode,)
    _node_accept_types = (AbstractField, AbstractLink)
    _link_accept_types = (AbstractOption,)
    _field_accept_types = (AbstractOption,)

    def __init__(self, items: t.List[Node], unions: t.List[Union]) -> None:
        self.items = items
        self.unions = unions
        self.errors = Errors()
        self._ctx: t.List = []

    @classmethod
    def validate(cls, items: t.List[Node], unions: t.List[Union]) -> None:
        validator = cls(items, unions)
        validator.visit_graph_items(items)
        validator.visit_graph_unions(unions)
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

        graph_nodes_map = {e.name for e in self.items if e.name is not None}
        unions_map = {u.name: u for u in self.unions}
        if obj.node not in graph_nodes_map:
            if obj.node not in unions_map:
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

    def visit_union(self, obj: "Union") -> t.Any:
        if not obj.name:
            self.errors.report("Union must have a name")

        if not obj.types:
            self.errors.report("Union must have at least one type")

        nodes_map = {e.name: e for e in self.items if e.name is not None}

        invalid = [
            type_ for type_ in obj.types if type_ not in nodes_map
        ]

        if invalid:
            self.errors.report(
                "Union '{}' types '{}' must point to node or data type".format(
                    obj.name, invalid
                )
            )
            return

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
