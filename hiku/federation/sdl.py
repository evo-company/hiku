from math import isfinite
from typing import (
    Optional,
    Iterable,
    List,
)

from graphql.language.printer import print_ast
from graphql.language import ast
from graphql.pyutils import inspect

from hiku.graph import (
    Link,
    Nothing,
    GraphVisitor,
    Field,
    Node,
    Root,
    GraphTransformer,
    Graph,
    Option,
)
from .directive import (
    Directive,
    Arg,
)
from hiku.types import (
    IntegerMeta,
    TypeRefMeta,
    StringMeta,
    SequenceMeta,
    OptionalMeta,
    AnyMeta,
    FloatMeta,
    BooleanMeta,
    Record,
)


def _name(value):
    return ast.NameNode(value=value) if value is not None else None


def coerce_type(x):
    if isinstance(x, str):
        return _name(x)
    return x


def _non_null_type(val):
    return ast.NonNullTypeNode(type=coerce_type(val))


def _encode_type(value) -> ast.TypeNode:
    def _encode(val):
        if isinstance(val, OptionalMeta):
            return _encode(val.__type__), True
        elif isinstance(val, TypeRefMeta):
            return val.__type_name__
        elif isinstance(val, IntegerMeta):
            return 'Int'
        elif isinstance(val, StringMeta):
            return 'String'
        elif isinstance(val, BooleanMeta):
            return 'Boolean'
        elif isinstance(val, SequenceMeta):
            return ast.ListTypeNode(type=_encode_type(val.__item_type__))
        elif isinstance(val, AnyMeta):
            return 'Any'
        elif isinstance(val, FloatMeta):
            return 'Float'
        elif val is None:
            return ''
        else:
            raise TypeError('Unsupported type: {!r}'.format(val))

    encoded = _encode(value)
    if isinstance(encoded, tuple):
        [type_, optional] = encoded
        if optional:
            return coerce_type(type_)
        return _non_null_type(type_)

    return _non_null_type(encoded)


def _encode_default_value(value) -> Optional[ast.ValueNode]:
    if value == Nothing:
        return None

    if value is None:
        return ast.NullValueNode()

    if isinstance(value, bool):
        return ast.BooleanValueNode(value=value)

    if isinstance(value, int):
        return ast.IntValueNode(value=f"{value:d}")
    if isinstance(value, float) and isfinite(value):
        return ast.FloatValueNode(value=f"{value:g}")

    if isinstance(value, str):
        return ast.StringValueNode(value=value)

    if isinstance(value, Iterable) and not isinstance(value, str):
        maybe_value_nodes = (_encode_default_value(item) for item in value)
        value_nodes = list(filter(None, maybe_value_nodes))
        return ast.ListValueNode(values=[value_nodes])

    raise TypeError(f"Cannot convert value to AST: {inspect(value)}.")


def _encode_directive_arg_type(type_, value) -> ast.ValueNode:
    def get_value_node(t, val):
        if isinstance(t, OptionalMeta):
            return get_value_node(t.__type__, val)
        elif isinstance(t, TypeRefMeta):
            return get_value_node(t.__type_name__, val)
        elif isinstance(t, IntegerMeta):
            return ast.IntValueNode(value=val)
        elif isinstance(t, StringMeta):
            return ast.StringValueNode(value=val)
        elif isinstance(t, BooleanMeta):
            return ast.BooleanValueNode(value=val)
        elif isinstance(t, SequenceMeta):
            return ast.ListValueNode(values=[
                get_value_node(t.__item_type__, v) for v in val
            ])
        elif isinstance(t, AnyMeta):
            return ast.StringValueNode(value=val)
        elif isinstance(t, FloatMeta):
            return ast.FloatValueNode(value=val)
        elif t is None:
            return ast.NullValueNode()
        else:
            raise TypeError('Unsupported arg type: {!r}'.format(value))

    return get_value_node(type_, value)


class Exporter(GraphVisitor):
    def visit_graph(self, obj: Graph) -> List[ast.DefinitionNode]:
        """List of ObjectTypeDefinitionNode and ObjectTypeExtensionNode"""
        return [
            self.get_any_type(),
            *[self.visit_record(type_name, type_)
              for type_name, type_ in obj.data_types.items()],
            *[self.visit(item) for item in obj.items]
        ]

    def get_any_type(self):
        return ast.ScalarTypeDefinitionNode(name=_name('Any'))

    def visit_root(self, obj: Root):
        return ast.ObjectTypeExtensionNode(
            name=_name('Query'),
            fields=[self.visit(item) for item in obj.fields],
            directives=[]
        )

    def visit_field(self, obj: Field):
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            type=_encode_type(obj.type),
            arguments=[self.visit_option(o) for o in obj.options],
            directives=[self.visit_directive(d) for d in obj.directives]
        )

    def visit_directive(self, obj: Directive):
        return ast.DirectiveNode(
            name=_name(obj.name),
            arguments=[self.visit_directive_arg(arg) for arg in obj.args]
        )

    def visit_directive_arg(self, arg: Arg):
        return ast.ArgumentNode(
            name=_name(arg.name),
            value=_encode_directive_arg_type(arg.type, arg.value)
        )

    def visit_node(self, obj: Node):
        fields = [self.visit(field) for field in obj.fields]

        return ast.ObjectTypeDefinitionNode(
            name=_name(obj.name),
            fields=fields,
            directives=[self.visit_directive(d) for d in obj.directives]
        )

    def visit_link(self, obj: Link):
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            arguments=[self.visit_option(o) for o in obj.options],
            type=_encode_type(obj.type)
        )

    def visit_option(self, obj: Option):
        return ast.InputValueDefinitionNode(
            name=_name(obj.name),
            description=obj.description,
            type=_encode_type(obj.type),
            default_value=_encode_default_value(obj.default),
        )

    def visit_record(self, type_name: str, obj: Record):
        def new_field(name: str, type_):
            return ast.FieldDefinitionNode(
                name=_name(name),
                type=_encode_type(type_),
            )
        fields = [new_field(f_name, field)
                  for f_name, field in obj.__field_types__.items()]
        return ast.ObjectTypeDefinitionNode(
            name=_name(type_name),
            fields=fields,
        )


def get_ast(graph: Graph) -> ast.DocumentNode:
    graph = _StripGraph().visit(graph)
    return ast.DocumentNode(definitions=Exporter().visit(graph))


class _StripGraph(GraphTransformer):
    def visit_root(self, obj):
        def skip(field):
            return field.name in ['__typename', '_entities']

        return Root([self.visit(f) for f in obj.fields if not skip(f)])

    def visit_graph(self, obj):
        def skip(node):
            if node.name is None:
                # check if it is a Root node from introspection
                return '__schema' in node.fields_map

            return node.name.startswith('__')

        return Graph(
            [self.visit(node) for node in obj.items if not skip(node)],
            obj.data_types
        )

    def visit_node(self, obj):
        def skip(field):
            return field.name in ['__typename']

        return Node(
            obj.name,
            fields=[self.visit(f) for f in obj.fields if not skip(f)],
            description=obj.description,
            directives=obj.directives
        )


def print_sdl(graph: Graph) -> str:
    """Print graphql AST into a string"""
    return print_ast(get_ast(graph))
