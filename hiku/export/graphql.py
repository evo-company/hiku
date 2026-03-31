from collections import OrderedDict
from typing import Any

from graphql.language import ast

from hiku.query import Fragment

from ..query import (
    Field,
    Link,
    Node,
    QueryVisitor,
)


def _name(value: Any) -> ast.NameNode | None:
    return ast.NameNode(value=value) if value is not None else None


def _encode(value: Any) -> ast.ValueNode:
    if value is None:
        return ast.NullValueNode()
    elif isinstance(value, bool):
        return ast.BooleanValueNode(value=value)
    elif isinstance(value, int):
        return ast.IntValueNode(value=str(value))
    elif isinstance(value, float):
        return ast.FloatValueNode(value=str(value))
    elif isinstance(value, str):
        return ast.StringValueNode(value=value)
    elif isinstance(value, list):
        return ast.ListValueNode(values=[_encode(v) for v in value])
    elif isinstance(value, dict):
        return ast.ObjectValueNode(
            fields=[
                ast.ObjectFieldNode(name=_name(key), value=_encode(val))
                for key, val in value.items()
            ]
        )
    else:
        raise TypeError("Unsupported type: {!r}".format(value))


class Exporter(QueryVisitor):
    def visit(self, obj: Any) -> Any:
        return obj.accept(self)

    def visit_field(self, obj: Field) -> ast.FieldNode:
        arguments = None
        if obj.options:
            arguments = [
                ast.ArgumentNode(name=_name(key), value=_encode(val))
                for key, val in obj.options.items()
            ]
        return ast.FieldNode(
            name=_name(obj.name),
            alias=_name(obj.alias),
            arguments=arguments,
        )

    def visit_link(self, obj: Link) -> ast.FieldNode:
        arguments = None
        if obj.options:
            arguments = [
                ast.ArgumentNode(name=_name(key), value=_encode(val))
                for key, val in obj.options.items()
            ]
        return ast.FieldNode(
            name=_name(obj.name),
            alias=_name(obj.alias),
            arguments=arguments,
            selection_set=self.visit(obj.node),
        )

    def visit_fragment(self, obj: Fragment) -> Any:
        if obj.name is None:
            return ast.InlineFragmentNode(
                type_condition=(
                    ast.NamedTypeNode(
                        name=_name(obj.type_name),
                    )
                    if obj.type_name is not None
                    else None
                ),
                selection_set=self.visit(obj.node),
            )

        return ast.FragmentSpreadNode(name=_name(obj.name))

    def visit_node(self, obj: Node) -> ast.SelectionSetNode:
        selections = []
        for f in obj.fields:
            selections.append(self.visit(f))

        for fr in obj.fragments:
            selections.append(self.visit(fr))

        return ast.SelectionSetNode(selections=selections)


class FragmentsCollector(QueryVisitor):
    def __init__(self) -> None:
        self.fragments: OrderedDict[str, Fragment] = OrderedDict()

    def collect(self, obj: Node) -> list[Fragment]:
        self.visit(obj)
        return list(self.fragments.values())

    def visit_node(self, obj: Node) -> None:
        for field in obj.fields:
            self.visit(field)

        for fragment in obj.fragments:
            self.visit(fragment)

    def visit_field(self, obj: Field) -> None:
        return None

    def visit_link(self, obj: Link) -> None:
        self.visit(obj.node)

    def visit_fragment(self, obj: Fragment) -> None:
        if obj.name is not None:
            if obj.name in self.fragments:
                return
            self.fragments[obj.name] = obj

        self.visit(obj.node)


def export(query: Node) -> ast.DocumentNode:
    exporter = Exporter()
    fragments = FragmentsCollector().collect(query)

    return ast.DocumentNode(
        definitions=[
            ast.OperationDefinitionNode(
                operation=ast.OperationType.QUERY,
                selection_set=exporter.visit(query),
            )
        ]
        + [
            ast.FragmentDefinitionNode(
                name=_name(fragment.name),
                type_condition=ast.NamedTypeNode(
                    name=_name(fragment.type_name),
                ),
                selection_set=exporter.visit(fragment.node),
            )
            for fragment in fragments
        ]
    )
