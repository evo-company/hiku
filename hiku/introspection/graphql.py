import re
import json
import typing as t

from functools import partial
from collections import OrderedDict

from ..directives import (
    Cached,
    Deprecated,
    Directive,
    _SkipDirective,
    _IncludeDirective,
    SchemaDirective,
    get_deprecated,
)
from ..graph import (
    Graph,
    Root,
    Node,
    Link,
    Option,
    Field,
    Nothing,
    NothingType,
)
from ..graph import GraphVisitor, GraphTransformer
from ..types import (
    IDMeta,
    ScalarMeta,
    TypeRef,
    String,
    Sequence,
    Boolean,
    Optional,
    AnyMeta,
    MappingMeta,
    CallableMeta,
    SequenceMeta,
    OptionalMeta,
    TypeRefMeta,
    StringMeta,
    IntegerMeta,
    FloatMeta,
    BooleanMeta,
    UnionRefMeta,
)
from ..types import Any, RecordMeta, AbstractTypeVisitor
from ..utils import (
    listify,
    cached_property,
)
from .types import (
    SCALAR,
    NON_NULL,
    LIST,
    INPUT_OBJECT,
    OBJECT,
    UNION,
    DIRECTIVE,
    FieldIdent,
    FieldArgIdent,
    InputObjectFieldIdent,
    DirectiveArgIdent,
    HashedNamedTuple,
)


# TODO(mkind): expose as public API
_BUILTIN_DIRECTIVES: t.Tuple[
    t.Union[t.Type[Directive], t.Type[SchemaDirective]], ...
] = (
    _SkipDirective,
    _IncludeDirective,
    Deprecated,
    Cached,
)

BUILTIN_SCALARS: t.Tuple[SCALAR, ...] = (  # type: ignore[valid-type]
    SCALAR("String"),
    SCALAR("Int"),
    SCALAR("Boolean"),
    SCALAR("Float"),
    SCALAR("Any"),
    SCALAR("ID"),
)


def _async_wrapper(func: t.Callable) -> t.Callable:
    async def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        return func(*args, **kwargs)

    return wrapper


QUERY_ROOT_NAME = "Query"
MUTATION_ROOT_NAME = "Mutation"


class SchemaInfo:
    def __init__(
        self,
        query_graph: Graph,
        mutation_graph: t.Optional[Graph],
        directives: t.Tuple[
            t.Union[t.Type[Directive], t.Type[SchemaDirective]], ...
        ],
    ):
        self.query_graph = query_graph
        self.data_types = query_graph.data_types
        self.mutation_graph = mutation_graph
        self.directives = directives or ()
        self.scalars = BUILTIN_SCALARS
        self.nodes_map = self._nodes_map()
        self.unions_map = self.query_graph.unions_map

    def _nodes_map(self) -> OrderedDict:
        nodes = [(n.name, n) for n in self.query_graph.nodes]
        nodes.append((QUERY_ROOT_NAME, self.query_graph.root))
        if self.mutation_graph is not None:
            nodes.append((MUTATION_ROOT_NAME, self.mutation_graph.root))
        return OrderedDict(nodes)

    @cached_property
    def directives_map(self) -> OrderedDict:
        return OrderedDict(
            (d.__directive_info__.name, d) for d in self.directives
        )

    @staticmethod
    def is_field_hidden(field: Field) -> bool:
        """Determines if a field should be hidden from introspection."""
        return field.name.startswith("_")


class TypeIdent(AbstractTypeVisitor):
    def __init__(self, graph: Graph, input_mode: bool = False) -> None:
        self._graph = graph
        self._input_mode = input_mode

    def visit_any(self, obj: AnyMeta) -> HashedNamedTuple:
        return SCALAR("Any")

    def visit_scalar(self, obj: ScalarMeta) -> HashedNamedTuple:
        return NON_NULL(SCALAR(obj.__type_name__))

    def visit_mapping(self, obj: MappingMeta) -> HashedNamedTuple:
        return SCALAR("Any")

    def visit_record(self, obj: RecordMeta) -> HashedNamedTuple:
        return SCALAR("Any")

    def visit_callable(self, obj: CallableMeta) -> t.NoReturn:
        raise TypeError("Not expected here: {!r}".format(obj))

    def visit_sequence(self, obj: SequenceMeta) -> HashedNamedTuple:
        return NON_NULL(LIST(self.visit(obj.__item_type__)))

    def visit_optional(self, obj: OptionalMeta) -> HashedNamedTuple:
        ident = self.visit(obj.__type__)
        return ident.of_type if isinstance(ident, NON_NULL) else ident

    def visit_typeref(self, obj: TypeRefMeta) -> HashedNamedTuple:
        if self._input_mode:
            assert (
                obj.__type_name__ in self._graph.data_types
            ), obj.__type_name__
            return NON_NULL(INPUT_OBJECT(obj.__type_name__))
        else:
            return NON_NULL(OBJECT(obj.__type_name__))

    def visit_unionref(self, obj: UnionRefMeta) -> t.Any:
        return NON_NULL(UNION(obj.__type_name__, tuple()))

    def visit_string(self, obj: StringMeta) -> HashedNamedTuple:
        return NON_NULL(SCALAR("String"))

    def visit_id(self, obj: IDMeta) -> t.Any:
        return NON_NULL(SCALAR("ID"))

    def visit_integer(self, obj: IntegerMeta) -> HashedNamedTuple:
        return NON_NULL(SCALAR("Int"))

    def visit_float(self, obj: FloatMeta) -> HashedNamedTuple:
        return NON_NULL(SCALAR("Float"))

    def visit_boolean(self, obj: BooleanMeta) -> HashedNamedTuple:
        return NON_NULL(SCALAR("Boolean"))


def not_implemented(*args: t.Any, **kwargs: t.Any) -> t.NoReturn:
    raise NotImplementedError(args, kwargs)


def na_maybe(schema: SchemaInfo) -> NothingType:
    return Nothing


def na_many(
    schema: SchemaInfo,
    ids: t.Optional[t.List] = None,
    options: t.Optional[t.Any] = None,
) -> t.List[t.List]:
    if ids is None:
        return []
    else:
        return [[] for _ in ids]


def schema_link(schema: SchemaInfo) -> None:
    return None


def type_link(
    schema: SchemaInfo, options: t.Dict
) -> t.Union[HashedNamedTuple, NothingType]:
    name = options["name"]
    if name in schema.nodes_map:
        return OBJECT(name)
    elif name in schema.unions_map:
        union = schema.unions_map[name]
        return UNION(
            union.name, tuple(OBJECT(type_name) for type_name in union.types)
        )
    else:
        return Nothing


@listify
def root_schema_types(schema: SchemaInfo) -> t.Iterator[HashedNamedTuple]:
    for scalar in schema.scalars:
        yield scalar

    for name in schema.nodes_map:
        yield OBJECT(name)

    for name, type_ in schema.data_types.items():
        if isinstance(type_, RecordMeta):
            yield OBJECT(name)
            yield INPUT_OBJECT(name)

    for union in schema.query_graph.unions:
        yield UNION(
            union.name, tuple(OBJECT(type_name) for type_name in union.types)
        )


def root_schema_query_type(schema: SchemaInfo) -> HashedNamedTuple:
    return OBJECT(QUERY_ROOT_NAME)


def root_schema_mutation_type(
    schema: SchemaInfo,
) -> t.Union[HashedNamedTuple, NothingType]:
    if schema.mutation_graph is not None:
        return OBJECT(MUTATION_ROOT_NAME)
    else:
        return Nothing


def root_schema_directives(schema: SchemaInfo) -> t.List[DIRECTIVE]:  # type: ignore[valid-type]  # noqa: E501
    return [
        DIRECTIVE(directive.__directive_info__.name)
        for directive in schema.directives
    ]


@listify
def type_info(
    schema: SchemaInfo, fields: t.List[Field], ids: t.List
) -> t.Iterator[t.List[t.Optional[t.Dict]]]:
    for ident in ids:
        if isinstance(ident, OBJECT):
            if ident.name in schema.nodes_map:
                description = schema.nodes_map[ident.name].description
            else:
                description = None
            info = {
                "id": ident,
                "kind": "OBJECT",
                "name": ident.name,
                "description": description,
            }
        elif isinstance(ident, INPUT_OBJECT):
            info = {
                "id": ident,
                "kind": "INPUT_OBJECT",
                "name": "IO{}".format(ident.name),
                "description": None,
            }
        elif isinstance(ident, NON_NULL):
            info = {"id": ident, "kind": "NON_NULL"}
        elif isinstance(ident, LIST):
            info = {"id": ident, "kind": "LIST"}
        elif isinstance(ident, SCALAR):
            info = {"id": ident, "name": ident.name, "kind": "SCALAR"}
        elif isinstance(ident, UNION):
            info = {
                "id": ident,
                "kind": "UNION",
                "name": ident.name,
                "description": schema.query_graph.unions_map[
                    ident.name
                ].description,
            }
        else:
            raise TypeError(repr(ident))
        yield [info.get(f.name) for f in fields]


@listify
def type_fields_link(
    schema: SchemaInfo, ids: t.List, options: t.List
) -> t.Iterator[t.List[HashedNamedTuple]]:
    for ident in ids:
        if isinstance(ident, OBJECT):
            if ident.name in schema.nodes_map:
                node = schema.nodes_map[ident.name]
                field_idents = [
                    FieldIdent(ident.name, f.name)
                    for f in node.fields
                    if not schema.is_field_hidden(f)
                ]
            else:
                type_ = schema.data_types[ident.name]
                field_idents = [
                    FieldIdent(ident.name, f_name)
                    for f_name, f_type in type_.__field_types__.items()
                ]
            if not field_idents:
                raise TypeError(
                    'Object type "{}" does not contain fields, '
                    "which is not acceptable for GraphQL in order "
                    "to define schema type".format(ident.name)
                )
            yield field_idents
        else:
            yield []


@listify
def type_of_type_link(
    schema: SchemaInfo, ids: t.List
) -> t.Iterator[t.Union[HashedNamedTuple, NothingType]]:
    for ident in ids:
        if isinstance(ident, (NON_NULL, LIST)):
            yield ident.of_type
        else:
            yield Nothing


@listify
def possible_types_type_link(schema: SchemaInfo, ids: t.List) -> t.Iterator:
    if ids is None:
        yield []

    for ident in ids:
        if isinstance(ident, UNION):
            yield ident.possible_types
        else:
            yield []


@listify
def field_info(
    schema: SchemaInfo, fields: t.List[Field], ids: t.List
) -> t.Iterator[t.List[t.Dict]]:
    for ident in ids:
        if ident.node in schema.nodes_map:
            node = schema.nodes_map[ident.node]
            field = node.fields_map[ident.name]
            deprecated = None
            if isinstance(field, (Field, Link)):
                deprecated = get_deprecated(field)

            info = {
                "id": ident,
                "name": field.name,
                "description": field.description,
                "isDeprecated": bool(deprecated),
                "deprecationReason": deprecated and deprecated.reason,
            }
        else:
            info = {
                "id": ident,
                "name": ident.name,
                "description": None,
                "isDeprecated": False,
                "deprecationReason": None,
            }
        yield [info[f.name] for f in fields]


@listify
def field_type_link(
    schema: SchemaInfo, ids: t.List
) -> t.Iterator[HashedNamedTuple]:
    type_ident = TypeIdent(schema.query_graph)
    for ident in ids:
        if ident.node in schema.nodes_map:
            node = schema.nodes_map[ident.node]
            field = node.fields_map[ident.name]
            yield type_ident.visit(field.type or Any)
        else:
            data_type = schema.data_types[ident.node]
            field_type = data_type.__field_types__[ident.name]
            yield type_ident.visit(field_type)


@listify
def field_args_link(
    schema: SchemaInfo, ids: t.List
) -> t.Iterator[t.List[HashedNamedTuple]]:
    for ident in ids:
        if ident.node in schema.nodes_map:
            node = schema.nodes_map[ident.node]
            field = node.fields_map[ident.name]
            yield [
                FieldArgIdent(ident.node, field.name, option.name)
                for option in field.options
            ]
        else:
            yield []


@listify
def type_input_object_input_fields_link(
    schema: SchemaInfo, ids: t.List
) -> t.Iterator[t.List[HashedNamedTuple]]:
    for ident in ids:
        if isinstance(ident, INPUT_OBJECT):
            data_type = schema.data_types[ident.name]
            yield [
                InputObjectFieldIdent(ident.name, key)
                for key in data_type.__field_types__.keys()
            ]
        else:
            yield []


@listify
def input_value_info(
    schema: SchemaInfo, fields: t.List[Field], ids: t.List[HashedNamedTuple]
) -> t.Iterator[t.List[t.Dict]]:
    for ident in ids:
        if isinstance(ident, FieldArgIdent):
            node = schema.nodes_map[ident.node]
            field = node.fields_map[ident.field]
            option = field.options_map[ident.name]
            if option.default is Nothing:
                default = None
            else:
                default = json.dumps(option.default)
            info = {
                "id": ident,
                "name": option.name,
                "description": option.description,
                "defaultValue": default,
            }
            yield [info[f.name] for f in fields]
        elif isinstance(ident, InputObjectFieldIdent):
            info = {
                "id": ident,
                "name": ident.key,
                "description": None,
                "defaultValue": None,
            }
            yield [info[f.name] for f in fields]
        elif isinstance(ident, DirectiveArgIdent):
            directive = schema.directives_map[ident.name]
            arg = directive.args_map()[ident.arg]
            info = {
                "id": ident,
                "name": arg.field_name,
                "description": arg.description,
                "defaultValue": arg.default_value,
            }
            yield [info[f.name] for f in fields]
        else:
            raise TypeError(repr(ident))


@listify
def input_value_type_link(
    schema: SchemaInfo, ids: t.List[HashedNamedTuple]
) -> t.Iterator[HashedNamedTuple]:
    type_ident = TypeIdent(schema.query_graph, input_mode=True)
    for ident in ids:
        if isinstance(ident, FieldArgIdent):
            node = schema.nodes_map[ident.node]
            field = node.fields_map[ident.field]
            option = field.options_map[ident.name]
            yield type_ident.visit(option.type)
        elif isinstance(ident, InputObjectFieldIdent):
            data_type = schema.data_types[ident.name]
            field_type = data_type.__field_types__[ident.key]
            yield type_ident.visit(field_type)
        elif isinstance(ident, DirectiveArgIdent):
            directive = schema.directives_map[ident.name]
            arg = directive.args_map()[ident.arg]
            yield arg.type_ident
        else:
            raise TypeError(repr(ident))


@listify
def directive_value_info(
    schema: SchemaInfo,
    fields: t.List[Field],
    ids: t.List[DIRECTIVE],  # type: ignore[valid-type]
) -> t.Iterator[t.List[Any]]:
    for ident in ids:
        if ident.name in schema.directives_map:  # type: ignore[attr-defined]
            info = schema.directives_map[ident.name].__directive_info__  # type: ignore  # noqa: E501
            data = {
                "name": info.name,
                "description": info.description,
                "locations": [loc.value for loc in info.locations],
            }
            yield [data[f.name] for f in fields]


def directive_args_link(
    schema: SchemaInfo, ids: t.List[str]
) -> t.List[t.List[DirectiveArgIdent]]:  # type: ignore[valid-type]
    links = []
    for ident in ids:
        directive = schema.directives_map[ident].__directive_info__
        links.append(
            [DirectiveArgIdent(ident, arg.name) for arg in directive.args]
        )
    return links


GRAPH = Graph(
    [
        Node(
            "__Type",
            [
                Field("id", None, type_info),
                Field("kind", String, type_info),
                Field("name", String, type_info),
                Field("description", String, type_info),
                # OBJECT and INTERFACE only
                Link(
                    "fields",
                    Sequence[TypeRef["__Field"]],
                    type_fields_link,
                    requires="id",
                    options=[
                        Option("includeDeprecated", Boolean, default=False)
                    ],
                ),
                # OBJECT only
                Link(
                    "interfaces",
                    Sequence[TypeRef["__Type"]],
                    na_many,
                    requires="id",
                ),
                # INTERFACE and UNION only
                Link(
                    "possibleTypes",
                    Sequence[TypeRef["__Type"]],
                    possible_types_type_link,
                    requires="id",
                ),
                # ENUM only
                Link(
                    "enumValues",
                    Sequence[TypeRef["__EnumValue"]],
                    # TODO: add enums handling
                    na_many,
                    requires="id",
                    options=[
                        Option("includeDeprecated", Boolean, default=False)
                    ],
                ),
                # INPUT_OBJECT only
                Link(
                    "inputFields",
                    Sequence[TypeRef["__InputValue"]],
                    type_input_object_input_fields_link,
                    requires="id",
                ),
                # NON_NULL and LIST only
                Link(
                    "ofType",
                    Optional[TypeRef["__Type"]],
                    type_of_type_link,
                    requires="id",
                ),
            ],
        ),
        Node(
            "__Field",
            [
                Field("id", None, field_info),
                Field("name", String, field_info),
                Field("description", String, field_info),
                Link(
                    "args",
                    Sequence[TypeRef["__InputValue"]],
                    field_args_link,
                    requires="id",
                ),
                Link("type", TypeRef["__Type"], field_type_link, requires="id"),
                Field("isDeprecated", Boolean, field_info),
                Field("deprecationReason", String, field_info),
            ],
        ),
        Node(
            "__InputValue",
            [
                Field("id", None, input_value_info),
                Field("name", String, input_value_info),
                Field("description", String, input_value_info),
                Link(
                    "type",
                    TypeRef["__Type"],
                    input_value_type_link,
                    requires="id",
                ),
                Field("defaultValue", String, input_value_info),
            ],
        ),
        Node(
            "__Directive",
            [
                Field("name", String, directive_value_info),
                Field("description", String, directive_value_info),
                Field("locations", Sequence[String], directive_value_info),
                Link(
                    "args",
                    Sequence[TypeRef["__InputValue"]],
                    directive_args_link,
                    requires="name",
                ),
            ],
        ),
        Node(
            "__EnumValue",
            [
                Field("name", String, not_implemented),
                Field("description", String, not_implemented),
                Field("isDeprecated", Boolean, not_implemented),
                Field("deprecationReason", String, not_implemented),
            ],
        ),
        Node(
            "__Schema",
            [
                Link(
                    "types",
                    Sequence[TypeRef["__Type"]],
                    root_schema_types,
                    requires=None,
                ),
                Link(
                    "queryType",
                    TypeRef["__Type"],
                    root_schema_query_type,
                    requires=None,
                ),
                Link(
                    "mutationType",
                    Optional[TypeRef["__Type"]],
                    root_schema_mutation_type,
                    requires=None,
                ),
                Link(
                    "subscriptionType",
                    Optional[TypeRef["__Type"]],
                    na_maybe,
                    requires=None,
                ),
                Link(
                    "directives",
                    Sequence[TypeRef["__Directive"]],
                    root_schema_directives,
                    requires=None,
                ),
            ],
        ),
        Root(
            [
                Link(
                    "__schema", TypeRef["__Schema"], schema_link, requires=None
                ),
                Link(
                    "__type",
                    Optional[TypeRef["__Type"]],
                    type_link,
                    requires=None,
                    options=[Option("name", String)],
                ),
            ]
        ),
    ]
)


class ValidateGraph(GraphVisitor):
    _name_re = re.compile(r"^[_a-zA-Z]\w*$", re.ASCII)

    def __init__(self) -> None:
        self._path: t.List[str] = []
        self._errors: t.List[str] = []

    def _add_error(self, name: str, description: str) -> None:
        path = ".".join(self._path + [name])
        self._errors.append("{}: {}".format(path, description))

    @classmethod
    def validate(cls, graph: Graph) -> None:
        self = cls()
        self.visit(graph)
        if self._errors:
            raise ValueError(
                "Invalid GraphQL graph:\n{}".format(
                    "\n".join("- {}".format(err) for err in self._errors)
                )
            )

    def visit_node(self, obj: Node) -> None:
        assert obj.name is not None
        if not self._name_re.match(obj.name):
            self._add_error(obj.name, "Invalid node name: {}".format(obj.name))
        if obj.fields:
            self._path.append(obj.name)
            super(ValidateGraph, self).visit_node(obj)
            self._path.pop()
        else:
            self._add_error(
                obj.name, "No fields in the {} node".format(obj.name)
            )

    def visit_root(self, obj: Root) -> None:
        if obj.fields:
            self._path.append("Root")
            super(ValidateGraph, self).visit_root(obj)
            self._path.pop()
        else:
            self._add_error("Root", "No fields in the Root node")

    def visit_field(self, obj: Field) -> None:
        if not self._name_re.match(obj.name):
            self._add_error(obj.name, "Invalid field name: {}".format(obj.name))
        super(ValidateGraph, self).visit_field(obj)

    def visit_link(self, obj: Link) -> None:
        if not self._name_re.match(obj.name):
            self._add_error(obj.name, "Invalid link name: {}".format(obj.name))
        super(ValidateGraph, self).visit_link(obj)

    def visit_option(self, obj: Option) -> None:
        if not self._name_re.match(obj.name):
            self._add_error(
                obj.name, "Invalid option name: {}".format(obj.name)
            )

        super(ValidateGraph, self).visit_option(obj)


class BindToSchema(GraphTransformer):
    def __init__(self, schema: SchemaInfo) -> None:
        self.schema = schema
        self._processed: t.Dict = {}

    def visit_field(self, obj: Field) -> Field:
        field = super(BindToSchema, self).visit_field(obj)
        func = self._processed.get(obj.func)
        if func is None:
            func = self._processed[obj.func] = partial(obj.func, self.schema)
        field.func = func
        return field

    def visit_link(self, obj: Link) -> Link:
        link = super(BindToSchema, self).visit_link(obj)
        link.func = partial(link.func, self.schema)
        return link


class MakeAsync(GraphTransformer):
    def __init__(self) -> None:
        self._processed: t.Dict = {}

    def visit_field(self, obj: Field) -> Field:
        field = super(MakeAsync, self).visit_field(obj)
        func = self._processed.get(obj.func)
        if func is None:
            func = self._processed[obj.func] = _async_wrapper(obj.func)
        field.func = func
        return field

    def visit_link(self, obj: Link) -> Link:
        link = super(MakeAsync, self).visit_link(obj)
        link.func = _async_wrapper(link.func)
        return link


def type_name_field_func(
    node_name: str, fields: t.List[Field], ids: t.Optional[t.List] = None
) -> t.List:
    return [[node_name] for _ in ids] if ids is not None else [node_name]


class AddIntrospection(GraphTransformer):
    def __init__(
        self, introspection_graph: Graph, type_name_field_factory: t.Callable
    ):
        self.introspection_graph = introspection_graph
        self.type_name_field_factory = type_name_field_factory

    def visit_node(self, obj: Node) -> Node:
        node = super(AddIntrospection, self).visit_node(obj)
        node.fields.append(self.type_name_field_factory(obj.name))
        return node

    def visit_root(self, obj: Root) -> Root:
        root = super(AddIntrospection, self).visit_root(obj)
        root.fields.append(self.type_name_field_factory(QUERY_ROOT_NAME))
        return root

    def visit_graph(self, obj: Graph) -> Graph:
        graph = super(AddIntrospection, self).visit_graph(obj)
        graph.items.extend(self.introspection_graph.items)
        return graph


class GraphQLIntrospection(GraphTransformer):
    """Adds GraphQL introspection into synchronous graph

    Example:

    .. code-block:: python

        from hiku.graph import apply
        from hiku.introspection.graphql import GraphQLIntrospection

        graph = apply(graph, [GraphQLIntrospection(graph)])

    """

    __directives__: t.Tuple[
        t.Union[t.Type[Directive], t.Type[SchemaDirective]], ...
    ] = _BUILTIN_DIRECTIVES

    def __init__(
        self,
        query_graph: Graph,
        mutation_graph: t.Optional[Graph] = None,
    ) -> None:
        """
        :param query_graph: graph, where Root node represents Query root
            operation type
        :param mutation_graph: graph, where Root node represents Mutation root
            operation type
        """
        self.schema = SchemaInfo(
            query_graph,
            mutation_graph,
            self.__directives__ + tuple(query_graph.directives or ()),
        )

    def __type_name__(self, node_name: t.Optional[str]) -> Field:
        return Field(
            "__typename", String, partial(type_name_field_func, node_name)
        )

    def __introspection_graph__(self) -> Graph:
        return BindToSchema(self.schema).visit(GRAPH)

    def visit_node(self, obj: Node) -> Node:
        node = super(GraphQLIntrospection, self).visit_node(obj)
        node.fields.append(self.__type_name__(obj.name))
        return node

    def visit_root(self, obj: Root) -> Root:
        root = super(GraphQLIntrospection, self).visit_root(obj)
        root.fields.append(self.__type_name__(QUERY_ROOT_NAME))
        return root

    def visit_graph(self, obj: Graph) -> Graph:
        ValidateGraph.validate(obj)
        introspection_graph = self.__introspection_graph__()
        items = [self.visit(node) for node in obj.items]
        items.extend(introspection_graph.items)
        return Graph(
            items,
            data_types=obj.data_types,
            directives=obj.directives,
            unions=obj.unions,
        )


class AsyncGraphQLIntrospection(GraphQLIntrospection):
    """Adds GraphQL introspection into asynchronous graph

    Example:

    .. code-block:: python

        from hiku.graph import apply
        from hiku.introspection.graphql import AsyncGraphQLIntrospection

        graph = apply(graph, [AsyncGraphQLIntrospection(graph)])

    """

    def __type_name__(self, node_name: t.Optional[str]) -> Field:
        return Field(
            "__typename",
            String,
            _async_wrapper(partial(type_name_field_func, node_name)),
        )

    def __introspection_graph__(self) -> Graph:
        graph = super(AsyncGraphQLIntrospection, self).__introspection_graph__()
        graph = MakeAsync().visit(graph)
        return graph
