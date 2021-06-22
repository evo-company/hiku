from math import isfinite
from typing import (
    Type,
    Optional,
)

from graphql.language.printer import print_ast
from graphql.language import ast
from graphql.pyutils import (
    inspect,
    FrozenList,
)

from hiku.graph import (
    Link,
    Nothing,
    GraphVisitor,
    Field,
    Node,
    Root,
    GraphTransformer,
    Graph,
)
from hiku.introspection.directive import (
    Directive,
    Arg,
)
from hiku.introspection.types import (
    NON_NULL,
    SCALAR,
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
)


def _name(value):
    return ast.NameNode(value=value) if value is not None else None


def _encode_type(value) -> ast.TypeNode:
    def coerce(x):
        if isinstance(x, str):
            return _name(x)
        return x

    def _non_null(val):
        return ast.NonNullTypeNode(type=coerce(val))

    # TODO refactor
    def not_null(func):
        def dec(*args, **kw):
            val = func(*args, **kw)
            if isinstance(val, tuple):
                (type_, optional) = val
                if optional:
                    return coerce(type_)
                return _non_null(type_)
            if kw.get('optional'):
                return val, True
            return _non_null(val)
        return dec

    @not_null
    def _encode(val, optional: bool = False):
        if isinstance(val, OptionalMeta):
            return _encode(val.__type__, optional=True)
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

    return _encode(value)


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

    raise TypeError(f"Cannot convert value to AST: {inspect(value)}.")


def _encode_option_type(value):
    """TODO seems like we can reuse encode from _encode_type"""
    if isinstance(value, IntegerMeta):
        # TODO NonNull
        return ast.NamedTypeNode(name=_name('Int'))
    if isinstance(value, StringMeta):
        return ast.NamedTypeNode(name=_name('String'))
    if isinstance(value, OptionalMeta):
        return _encode_option_type(value.__type__)
    elif isinstance(value, SequenceMeta):
        return ast.ListTypeNode(type=_encode_type(value.__item_type__))
    else:
        raise TypeError('Unsupported option type: {!r}'.format(value))


def _encode_directive_arg_type(value) -> Type[ast.ValueNode]:
    def _encode(val):
        if val == 'String':
            return ast.StringValueNode

    if isinstance(value, NON_NULL):
        return _encode_directive_arg_type(value.of_type)
    elif isinstance(value, SCALAR):
        return _encode(value.name)
    else:
        raise TypeError('Unsupported arg type: {!r}'.format(value))


# GraphVisitor
class Exporter(GraphVisitor):
    def visit_graph(self, obj: Graph):
        """List of ObjectTypeDefinitionNode and ObjectTypeExtensionNode"""
        return [self.visit(item) for item in obj.items]

    def visit_root(self, obj: Root):
        return ast.ObjectTypeExtensionNode(
            name=_name('Query'),
            fields=[self.visit(item) for item in obj.fields],
            directives=[]
        )

    def visit_field(self, obj: Field):
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            type=_encode_type(obj.type)
        )

    def visit_directive(self, obj: Directive):
        return ast.DirectiveNode(
            name=_name(obj.name),
            arguments=FrozenList([self.visit_directive_arg(arg) for arg in obj.args])
        )

    def visit_directive_arg(self, arg: Arg):
        return ast.ArgumentNode(
            name=_name(arg.name),
            value=_encode_directive_arg_type(arg.type)(value=arg.value)
        )

    def visit_node(self, obj: Node):
        fields = [self.visit_field(field) for field in obj.fields]

        directives = []
        if obj.directives:
            directives = FrozenList([self.visit_directive(d) for d in obj.directives])

        return ast.ObjectTypeDefinitionNode(
            name=_name(obj.name),
            fields=fields,
            directives=directives
        )

    def visit_link(self, obj: Link):
        arguments = []
        if obj.options:
            for opt in obj.options:
                arguments.append(ast.InputValueDefinitionNode(
                    name=_name(opt.name),
                    description=opt.description,
                    type=_encode_type(opt.type),
                    default_value=_encode_default_value(opt.default),
                ))
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            arguments=arguments,
            type=_encode_type(obj.type)
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
