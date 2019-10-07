from graphql.language import ast

from ..query import QueryVisitor, Field


def _name(value):
    return ast.NameNode(value=value) if value is not None else None


def _encode(value):
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
        return ast.ObjectValueNode(fields=[
            ast.ObjectFieldNode(name=_name(key), value=_encode(val))
            for key, val in value.items()
        ])
    else:
        raise TypeError('Unsupported type: {!r}'.format(value))


class Exporter(QueryVisitor):

    def visit_field(self, obj: Field):
        arguments = None
        if obj.options:
            arguments = [ast.ArgumentNode(name=_name(key), value=_encode(val))
                         for key, val in obj.options.items()]
        return ast.FieldNode(
            name=_name(obj.name),
            alias=_name(obj.alias),
            arguments=arguments,
        )

    def visit_link(self, obj):
        arguments = None
        if obj.options:
            arguments = [ast.ArgumentNode(name=_name(key), value=_encode(val))
                         for key, val in obj.options.items()]
        return ast.FieldNode(
            name=_name(obj.name),
            alias=_name(obj.alias),
            arguments=arguments,
            selection_set=self.visit(obj.node),
        )

    def visit_node(self, obj):
        return ast.SelectionSetNode(
            selections=[self.visit(f) for f in obj.fields],
        )


def export(query):
    return ast.DocumentNode(definitions=[
        ast.OperationDefinitionNode(
            operation=ast.OperationType.QUERY,
            selection_set=Exporter().visit(query),
        )
    ])
