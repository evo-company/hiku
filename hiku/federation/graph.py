import typing as t
from inspect import isawaitable

from hiku.federation.version import DEFAULT_FEDERATION_VERSION

from hiku.engine import pass_context

from hiku.directives import SchemaDirective
from hiku.enum import BaseEnum
from hiku.federation.utils import get_entity_types
from hiku.scalar import Scalar
from hiku.federation.scalars import _Any, FieldSet, LinkImport

from hiku.types import Optional, Record, Sequence, String, TypeRef, UnionRef

from hiku.graph import (
    Field,
    Graph as _Graph,
    GraphTransformer,
    Interface,
    Link,
    Node,
    Option,
    Root,
    Union,
)


class FederatedNode(Node):
    def __init__(
        self,
        name: t.Optional[str],
        fields: t.List[t.Union[Field, Link]],
        *,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
        resolve_reference: t.Optional[t.Callable] = None,
    ):
        super().__init__(
            name, fields, description=description, directives=directives
        )
        self.resolve_reference = resolve_reference


class GraphInit(GraphTransformer):
    type_to_resolve_reference_map: t.Dict[str, t.Callable]
    is_async: bool
    has_entity_types: bool

    @classmethod
    def init(
        cls,
        items: t.List[t.Union[FederatedNode, Node]],
        is_async: bool,
        has_entity_types: bool = False,
    ) -> t.List[Node]:
        self = cls()
        self.type_to_resolve_reference_map = {}
        self.is_async = is_async
        self.has_entity_types = has_entity_types
        return [self.visit(i) for i in items]

    def visit_root(self, root: Root) -> Root:
        if not self.has_entity_types:
            return root

        fields = root.fields[:]
        if "_entities" not in root.fields_map:
            fields.append(self.entities_link())
        if "_service" not in root.fields_map:
            fields.append(self.service_field())

        return Root(fields)

    def visit_node(self, obj: Node) -> Node:
        if hasattr(obj, "resolve_reference") and obj.name is not None:
            self.type_to_resolve_reference_map[obj.name] = obj.resolve_reference

        return super(GraphInit, self).visit_node(obj)

    def entities_link(self) -> Link:
        def entities_resolver(
            options: t.Dict,
        ) -> t.List[t.Tuple[t.Any, t.Type[TypeRef]]]:
            representations = options["representations"]
            if not representations:
                return []

            typ = representations[0]["__typename"]

            if typ not in self.type_to_resolve_reference_map:
                raise TypeError(
                    'Type "{}" must have "reference_resolver"'.format(typ)
                )

            resolve_reference = self.type_to_resolve_reference_map[typ]
            return [
                (r, TypeRef[typ]) for r in resolve_reference(representations)
            ]

        def _asyncify(func: t.Callable) -> t.Callable:
            async def wrapper(*args: t.Any, **kwargs: t.Any) -> t.List[t.Tuple]:
                result = []
                for item in func(*args, **kwargs):
                    if isawaitable(item[0]):
                        item[0] = await item[0]
                    result.append(item)
                return result

            return wrapper

        return Link(
            "_entities",
            Sequence[Optional[UnionRef["_Entity"]]],
            (
                _asyncify(entities_resolver)
                if self.is_async
                else entities_resolver
            ),
            options=[
                Option("representations", Sequence[_Any]),
            ],
            requires=None,
        )

    def service_field(self) -> Field:
        @pass_context
        def service_resolver(
            ctx: t.Dict,
            fields: t.List,
        ) -> t.List:
            return [{"sdl": ctx["__sdl__"]}]

        def _async(func: t.Callable) -> t.Callable:
            @pass_context
            async def wrapper(*args: t.Any, **kwargs: t.Any) -> t.List[t.Dict]:
                return func(*args, **kwargs)

            return wrapper

        return Field(
            "_service",
            TypeRef["_Service"],
            _async(service_resolver) if self.is_async else service_resolver,  # type: ignore[arg-type]  # noqa: E501
        )


class Graph(_Graph):
    def __init__(
        self,
        items: t.List[t.Union[FederatedNode, Node]],
        data_types: t.Optional[t.Dict[str, t.Type[Record]]] = None,
        directives: t.Optional[t.Sequence[t.Type[SchemaDirective]]] = None,
        unions: t.Optional[t.List[Union]] = None,
        interfaces: t.Optional[t.List[Interface]] = None,
        enums: t.Optional[t.List[BaseEnum]] = None,
        scalars: t.Optional[t.List[t.Type[Scalar]]] = None,
        is_async: bool = False,
    ):
        self.is_async = is_async

        if unions is None:
            unions = []

        if scalars is None:
            scalars = []

        unions_map = {union.name: union for union in unions}
        scalars_map = {scalar.__type_name__: scalar for scalar in scalars}

        entity_types = get_entity_types(items, DEFAULT_FEDERATION_VERSION)
        if entity_types:
            if "_Entity" not in unions_map:
                unions.append(Union("_Entity", entity_types))

        for scalar in [_Any, FieldSet, LinkImport]:
            if scalar.__type_name__ not in scalars_map:
                scalars.append(scalar)

        if data_types is None:
            data_types = {}

        if "_Service" not in data_types:
            data_types["_Service"] = Record[{"sdl": String}]

        items = GraphInit.init(items, is_async, bool(entity_types))

        super().__init__(
            items, data_types, directives, unions, interfaces, enums, scalars
        )

    @classmethod
    def from_graph(
        cls,
        other: "Graph",
        root: Root,
    ) -> "Graph":
        """Create graph from other graph, with new root node.
        Useful for creating mutation graph from query graph.
        """
        return cls(
            other.nodes + [root],
            data_types=other.data_types,
            directives=other.directives,
            unions=other.unions,
            interfaces=other.interfaces,
            enums=other.enums,
            scalars=other.scalars,
            is_async=other.is_async,
        )
