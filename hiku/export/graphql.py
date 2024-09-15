from typing import (
    Any,
    Optional,
)

from graphql.language import ast

from hiku.query import Fragment

from ..query import (
    QueryVisitor,
    Field,
    Node,
    Link,
)


def _name(value: Any) -> Optional[ast.NameNode]:
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


def export(query: Node) -> ast.DocumentNode:
    return ast.DocumentNode(
        definitions=[
            ast.OperationDefinitionNode(
                operation=ast.OperationType.QUERY,
                selection_set=Exporter().visit(query),
            )
        ]
    )
