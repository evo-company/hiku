from graphql import (
    NonNullTypeNode,
    ListTypeNode,
)
from graphql.language.printer import print_ast
from graphql.language import ast

from hiku.graph import (
    Link,
    Nothing,
)
from hiku.query import QueryVisitor
from hiku.types import (
    IntegerMeta,
    TypeRefMeta,
    StringMeta,
    SequenceMeta,
    OptionalMeta,
)


def _name(value):
    return ast.NameNode(value=value) if value is not None else None


def _encode_type(value, optional=False):
    def _maybe_non_null(val):
        coerce = lambda x: x
        if isinstance(val, str):
            coerce = _name

        return (
            NonNullTypeNode(type=coerce(val)) if not optional else coerce(val)
        )

    def _encode(val):
        if isinstance(value, OptionalMeta):
            return _encode_type(val.__type__, True)
        elif isinstance(val, TypeRefMeta):
            return val.__type_name__
        elif isinstance(val, IntegerMeta):
            return 'Int'
        elif isinstance(val, StringMeta):
            return 'String'
        elif isinstance(val, SequenceMeta):
            return ListTypeNode(type=_encode_type(val.__item_type__))
        else:
            raise TypeError('Unsupported type: {!r}'.format(val))

    return _maybe_non_null(_encode(value))


def _encode_default_value(value):
    return None if value == Nothing else value


def _encode_option_type(value):
    if isinstance(value, IntegerMeta):
        # TODO NonNull
        return ast.NamedTypeNode(name=_name('Int'))
    else:
        raise TypeError('Unsupported option type: {!r}'.format(value))


class Exporter(QueryVisitor):
    def visit_node(self, obj):
        fields = []
        for field in obj.fields:
            fields.append(ast.FieldDefinitionNode(
                name=_name(field.name),
                type=_encode_type(field.type)
            ))

        key_directives = []
        for key in obj.keys:
            key_directives.append(ast.DirectiveNode(
                name=_name('key'),
                arguments=[ast.ArgumentNode(
                    name=_name("fields"),
                    value=ast.StringValueNode(value=key)
                )]
            ))
        return ast.ObjectTypeDefinitionNode(
            name=_name(obj.name),
            fields=fields,
            directives=key_directives
        )

    def visit_link(self, obj: Link):
        arguments = []
        if obj.options:
            for opt in obj.options:
                arguments.append(ast.InputValueDefinitionNode(
                    name=_name(opt.name),
                    description=opt.description,
                    type=_encode_option_type(opt.type),
                    default_value=_encode_default_value(opt.default),
                ))
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            arguments=arguments,
            type=_encode_type(obj.type)
        )


def get_ast(value) -> ast.DocumentNode:
    return ast.DocumentNode(definitions=[
        ast.OperationDefinitionNode(
            operation=ast.OperationType.QUERY,
            selection_set=Exporter().visit(value),
        )
    ])


def print_sdl(value) -> str:
    return print_ast(get_ast(value))
