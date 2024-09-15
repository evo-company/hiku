import typing as t

from math import isfinite
from typing import (
    Optional,
    Iterable,
    List,
)

from graphql.language.printer import print_ast
from graphql.language import ast
from graphql.pyutils import inspect

from hiku.federation.utils import get_entity_types
from hiku.federation.version import DEFAULT_FEDERATION_VERSION

from hiku.directives import SchemaDirective
from hiku.federation.graph import Graph as FederationGraph
from hiku.federation.directive import (
    ComposeDirective,
    Extends,
    FederationSchemaDirective,
    Key,
    Link as LinkDirective,
)
from hiku.introspection.graphql import _BUILTIN_DIRECTIVES
from hiku.graph import (
    Link,
    Nothing,
    GraphVisitor,
    Field,
    Node,
    Root,
    GraphTransformer,
    Option,
    Graph,
    Union,
)
from hiku.scalar import ScalarMeta
from hiku.types import (
    EnumRefMeta,
    UnionRefMeta,
    IDMeta,
    IntegerMeta,
    MappingMeta,
    String,
    TypeRefMeta,
    StringMeta,
    SequenceMeta,
    OptionalMeta,
    AnyMeta,
    FloatMeta,
    BooleanMeta,
    GenericMeta,
)


def _name(value: t.Optional[str]) -> t.Optional[ast.NameNode]:
    return ast.NameNode(value=value) if value is not None else None


_BUILTIN_DIRECTIVES_NAMES = {
    directive.__directive_info__.name for directive in _BUILTIN_DIRECTIVES
}

_BUILTIN_SCALARS = [ast.ScalarTypeDefinitionNode(name=_name("Any"))]


@t.overload
def coerce_type(x: str) -> ast.NameNode: ...


@t.overload
def coerce_type(x: ast.Node) -> ast.Node: ...


def coerce_type(x):  # type: ignore[no-untyped-def]
    if isinstance(x, str):
        return _name(x)
    if not isinstance(x, ast.Node):
        raise TypeError("Unsupported type: {!r}".format(x))
    return x


def _non_null_type(val: t.Union[str, ast.Node]) -> ast.NonNullTypeNode:
    return ast.NonNullTypeNode(type=coerce_type(val))


def _encode_type(
    value: t.Any, input_type: bool = False
) -> t.Union[ast.NonNullTypeNode, ast.NameNode]:
    def _encode(
        val: t.Optional[GenericMeta],
    ) -> t.Union[str, t.Tuple, ast.ListTypeNode]:
        if isinstance(val, OptionalMeta):
            return _encode(val.__type__), True
        elif isinstance(val, TypeRefMeta):
            if input_type:
                return f"IO{val.__type_name__}"
            return val.__type_name__
        elif isinstance(val, EnumRefMeta):
            return val.__type_name__
        elif isinstance(val, UnionRefMeta):
            return val.__type_name__
        elif isinstance(val, ScalarMeta):
            return val.__type_name__
        elif isinstance(val, IntegerMeta):
            return "Int"
        elif isinstance(val, StringMeta):
            return "String"
        elif isinstance(val, IDMeta):
            return "ID"
        elif isinstance(val, BooleanMeta):
            return "Boolean"
        elif isinstance(val, SequenceMeta):
            return ast.ListTypeNode(
                type=_encode_type(val.__item_type__, input_type)
            )
        elif isinstance(val, AnyMeta):
            return "Any"
        elif isinstance(val, MappingMeta):
            return "Any"
        elif isinstance(val, FloatMeta):
            return "Float"
        elif val is None:
            return "Any"
        else:
            raise TypeError("Unsupported type: {!r}".format(val))

    encoded = _encode(value)
    if isinstance(encoded, tuple):
        [type_, optional] = encoded
        if optional:
            return coerce_type(type_)
        return _non_null_type(type_)

    return _non_null_type(encoded)


def _encode_default_value(value: t.Any) -> Optional[ast.ValueNode]:
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
        value_nodes: t.List[ast.ValueNode] = list(
            filter(None, maybe_value_nodes)
        )
        return ast.ListValueNode(values=value_nodes)

    raise TypeError(f"Cannot convert value to AST: {inspect(value)}.")


def schema_to_graphql_directive(
    directive: SchemaDirective,
    skip_fields: t.Optional[t.List[str]] = None,
) -> ast.DirectiveNode:
    skip_fields = skip_fields or []

    info = directive.__directive_info__
    arguments = []
    for arg in info.args:
        if arg.field_name in skip_fields:
            continue

        arguments.append(
            ast.ArgumentNode(
                name=_name(arg.field_name),
                value=_encode_default_value(getattr(directive, arg.name)),
            )
        )

    return ast.DirectiveNode(
        name=_name(info.name),
        arguments=arguments,
    )


class Exporter(GraphVisitor):
    def __init__(
        self,
        graph: Graph,
        mutation_graph: Optional[Graph],
        federation_version: int,
    ):
        self.graph = graph
        self.mutation_graph = mutation_graph
        self.federation_version = federation_version

    def export_data_types(
        self,
    ) -> t.Iterator[
        t.Union[ast.ObjectTypeDefinitionNode, ast.InputObjectTypeDefinitionNode]
    ]:
        for type_name, type_ in self.graph.data_types.items():
            yield ast.ObjectTypeDefinitionNode(
                name=_name(type_name),
                fields=[
                    ast.FieldDefinitionNode(
                        name=_name(f_name),
                        type=_encode_type(field),
                    )
                    for f_name, field in type_.__field_types__.items()
                ],
            )
            yield ast.InputObjectTypeDefinitionNode(
                name=_name(f"IO{type_name}"),
                fields=[
                    ast.InputValueDefinitionNode(
                        name=_name(f_name),
                        type=_encode_type(field, input_type=True),
                    )
                    for f_name, field in type_.__field_types__.items()
                ],
            )

    def visit_graph(self, graph: Graph) -> List[ast.DefinitionNode]:
        nodes: t.List[ast.DefinitionNode] = []

        for node in [
            self.get_schema_node(),
            *self.get_custom_directives(),
            *self.export_data_types(),
            *[self.visit(item) for item in graph.items],
            *(
                [self.get_mutation_root(self.mutation_graph)]
                if self.mutation_graph
                else []
            ),
            *self.export_scalars(),
            *self.export_enums(),
            *self.export_unions(),
            self.get_service_type(),
        ]:
            if node:
                nodes.append(node)

        return nodes

    def get_mutation_root(self, graph: Graph) -> ast.ObjectTypeExtensionNode:
        return ast.ObjectTypeExtensionNode(
            name=_name("Mutation"),
            fields=[self.visit(item) for item in graph.iter_root()],
        )

    def _iter_directives(self) -> t.Iterator[SchemaDirective]:
        """Return nodes + fields directives"""
        visited = set()
        for node in self.graph.nodes:
            for directive in node.directives:
                info = directive.__directive_info__
                if info.name not in visited:
                    visited.add(info.name)
                    yield directive

                for field in node.fields:
                    for directive in field.directives:
                        info = directive.__directive_info__
                        if info.name not in visited:
                            visited.add(info.name)
                            yield directive

    def get_schema_node(self) -> t.Optional[ast.SchemaExtensionNode]:
        if self.federation_version == 1:
            return None

        directives_in_use: List[str] = []

        for directive in self._iter_directives():
            info = directive.__directive_info__
            if (
                isinstance(directive, FederationSchemaDirective)
                and not info.compose_options
            ):
                directives_in_use.append(info.name)

        compose_directives_in_use: List[t.Type[FederationSchemaDirective]] = []

        for custom_directive in self.graph.directives:
            if issubclass(custom_directive, FederationSchemaDirective):
                info = custom_directive.__directive_info__
                if info.compose_options:
                    compose_directives_in_use.append(custom_directive)

        if compose_directives_in_use:
            directives_in_use.append("composeDirective")

        schema_directives = []

        link_default = LinkDirective(
            "https://specs.apollo.dev/federation/v2.3",
            None,
            None,
            [f"@{d}" for d in directives_in_use],  # type: ignore
        )

        schema_directives.append(
            schema_to_graphql_directive(link_default, skip_fields=["as", "for"])
        )

        for compose_directive in compose_directives_in_use:
            info = compose_directive.__directive_info__
            import_url = info.compose_options.import_url

            # import url is required by Apollo Federation, but since it is not
            # used in any validations we can provide a default url.
            if import_url is None:
                import_url = (
                    f"https://directives.hiku.evo.company/{info.name}/v0.1"
                )

            schema_directives.append(
                schema_to_graphql_directive(
                    LinkDirective(
                        import_url,
                        None,
                        None,
                        [f"@{info.name}"],  # type: ignore
                    ),
                    skip_fields=["as", "for"],
                )
            )

            schema_directives.append(
                schema_to_graphql_directive(ComposeDirective(f"@{info.name}"))
            )

        return ast.SchemaExtensionNode(
            directives=schema_directives,
            operation_types=[],
        )

    def get_custom_directives(self) -> t.List[ast.DirectiveDefinitionNode]:
        directives = []
        for d in self.graph.directives:
            info = d.__directive_info__
            directives.append(
                ast.DirectiveDefinitionNode(
                    description=(
                        _encode_default_value(info.description)
                        if info.description
                        else None
                    ),
                    name=_name(info.name),
                    arguments=[
                        ast.InputValueDefinitionNode(
                            name=_name(arg.field_name),
                            description=(
                                _encode_default_value(arg.description)
                                if arg.description
                                else None
                            ),
                            type=_encode_type(arg.type_ident),
                            default_value=_encode_default_value(
                                arg.default_value
                            ),
                        )
                        for arg in info.args
                    ],
                    repeatable=info.repeatable,
                    locations=[_name(loc.value) for loc in info.locations],
                )
            )
        return directives

    def export_scalars(self) -> t.List[ast.ScalarTypeDefinitionNode]:
        scalars = []
        for scalar in self.graph.scalars:
            if hasattr(scalar, "__federation_versions__"):
                if (
                    self.federation_version
                    not in scalar.__federation_versions__
                ):  # noqa: E501
                    continue

            scalars.append(
                ast.ScalarTypeDefinitionNode(
                    name=_name(scalar.__type_name__),
                )
            )
        return _BUILTIN_SCALARS + scalars

    def export_enums(self) -> t.List[ast.EnumTypeDefinitionNode]:
        enums = []
        for enum in self.graph.enums:
            enums.append(
                ast.EnumTypeDefinitionNode(
                    name=_name(enum.name),
                    values=[
                        ast.EnumValueDefinitionNode(name=_name(value.name))
                        for value in enum.values
                    ],
                )
            )
        return enums

    def export_unions(self) -> t.List[ast.UnionTypeDefinitionNode]:
        unions = []
        for union in self.graph.unions:
            unions.append(
                ast.UnionTypeDefinitionNode(
                    name=_name(union.name),
                    types=[
                        ast.NamedTypeNode(name=_name(type_))
                        for type_ in union.types
                    ],
                )
            )
        return unions

    def get_service_type(self) -> ast.ObjectTypeDefinitionNode:
        return ast.ObjectTypeDefinitionNode(
            name=_name("_Service"),
            fields=[
                ast.FieldDefinitionNode(
                    name=_name("sdl"),
                    type=_encode_type(String),
                ),
            ],
        )

    def visit_root(self, obj: Root) -> ast.ObjectTypeExtensionNode:
        return ast.ObjectTypeExtensionNode(
            name=_name("Query"),
            fields=[self.visit(item) for item in obj.fields],
        )

    def visit_field(self, obj: Field) -> ast.FieldDefinitionNode:
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            type=_encode_type(obj.type),
            arguments=[self.visit(o) for o in obj.options],
            directives=[self.visit(d) for d in obj.directives],
            description=(
                _encode_default_value(obj.description)
                if obj.description
                else None
            ),
        )

    def visit_node(
        self, obj: Node
    ) -> t.Union[ast.ObjectTypeDefinitionNode, ast.ObjectTypeExtensionNode]:
        fields = [
            self.visit(field)
            for field in obj.fields
            if not field.name.startswith("_")
        ]
        _Node: t.Union[
            t.Type[ast.ObjectTypeDefinitionNode],
            t.Type[ast.ObjectTypeExtensionNode],
        ] = ast.ObjectTypeDefinitionNode
        directives = []
        for directive in obj.directives:
            if isinstance(directive, Extends):
                _Node = ast.ObjectTypeExtensionNode
            else:
                directives.append(self.visit(directive))

        return _Node(name=_name(obj.name), fields=fields, directives=directives)

    def visit_link(self, obj: Link) -> ast.FieldDefinitionNode:
        return ast.FieldDefinitionNode(
            name=_name(obj.name),
            arguments=[self.visit(o) for o in obj.options],
            type=_encode_type(obj.type),
            directives=[self.visit(d) for d in obj.directives],
        )

    def visit_option(self, obj: Option) -> ast.InputValueDefinitionNode:
        return ast.InputValueDefinitionNode(
            name=_name(obj.name),
            description=(
                _encode_default_value(obj.description)
                if obj.description
                else None
            ),
            type=_encode_type(obj.type, input_type=True),
            default_value=_encode_default_value(obj.default),
        )

    def visit_schema_directive(
        self, directive: SchemaDirective
    ) -> ast.DirectiveNode:
        if isinstance(directive, Key) and self.federation_version == 1:
            # To support Apollo Federation v1, we need to drop resolvable field
            # from @key directive usage
            return schema_to_graphql_directive(
                directive, skip_fields=["resolvable"]
            )

        return schema_to_graphql_directive(directive)


def get_ast(
    graph: t.Union[Graph, FederationGraph],
    mutation_graph: Optional[t.Union[Graph, FederationGraph]],
    federation_version: int,
) -> ast.DocumentNode:
    graph = _StripGraph(federation_version).visit(graph)
    if mutation_graph is not None:
        mutation_graph = _StripGraph(federation_version).visit(mutation_graph)
    return ast.DocumentNode(
        definitions=Exporter(graph, mutation_graph, federation_version).visit(
            graph
        )
    )


class _StripGraph(GraphTransformer):
    def __init__(self, federation_version: int):
        self.federation_version = federation_version

    def visit_root(self, obj: Root) -> Root:
        def skip(field: t.Union[Field, Link]) -> bool:
            return field.name in ["__typename", "_entities", "_service"]

        return Root([self.visit(f) for f in obj.fields if not skip(f)])

    def visit_graph(self, obj: Graph) -> Graph:
        def skip(node: Node) -> bool:
            if node.name is None:
                # check if it is a Root node from introspection
                return "__schema" in node.fields_map

            return node.name.startswith("__")

        data_types = {
            name: type_
            for name, type_ in obj.data_types.items()
            if not name.startswith("_Service")
        }

        entities = get_entity_types(
            obj.nodes, federation_version=self.federation_version
        )
        unions = []
        for u in obj.unions:
            if u.name == "_Entity" and entities:
                unions.append(Union("_Entity", entities))
            else:
                unions.append(u)

        return Graph(
            [self.visit(node) for node in obj.items if not skip(node)],
            data_types,
            obj.directives,
            unions,
            obj.interfaces,
            obj.enums,
            obj.scalars,
        )

    def visit_node(self, obj: Node) -> Node:
        def skip(field: t.Union[Field, Link]) -> bool:
            return field.name in ["__typename"]

        return Node(
            obj.name,
            fields=[self.visit(f) for f in obj.fields if not skip(f)],
            description=obj.description,
            directives=obj.directives,
            implements=obj.implements,
        )


def print_sdl(
    graph: FederationGraph,
    mutation_graph: Optional[Graph] = None,
    federation_version: int = DEFAULT_FEDERATION_VERSION,
) -> str:
    """Print graphql AST into a string"""
    return print_ast(get_ast(graph, mutation_graph, federation_version))
