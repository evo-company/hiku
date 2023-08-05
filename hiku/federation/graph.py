import typing as t
from inspect import isawaitable

from hiku.directives import SchemaDirective
from hiku.enum import BaseEnum
from hiku.federation.utils import get_entity_types
from hiku.scalar import Scalar
from hiku.federation.scalars import _Any, FieldSet, LinkImport

from hiku.types import Optional, Record, Sequence, TypeRef, UnionRef

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

        return Root(
            root.fields
            + [
                self.entities_link(),
            ]
        )

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

        async def entities_resolver_async(
            options: t.Dict,
        ) -> t.List[t.Tuple[t.Any, t.Type[TypeRef]]]:
            representations = options["representations"]
            if not representations:
                return []

            typ = representations[0]["__typename"]

            if typ not in self.type_to_resolve_reference_map:
                raise TypeError(
                    'Type "{}" must have "resolve_reference" function'.format(
                        typ
                    )
                )

            resolve_reference = self.type_to_resolve_reference_map[typ]
            coro = resolve_reference(representations)
            if isawaitable(coro):
                return [(r, TypeRef[typ]) for r in await coro]

            return [(r, TypeRef[typ]) for r in coro]

        return Link(
            "_entities",
            Sequence[Optional[UnionRef["_Entity"]]],
            entities_resolver_async if self.is_async else entities_resolver,
            options=[
                Option("representations", Sequence[_Any]),
            ],
            requires=None,
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
        if unions is None:
            unions = []

        entity_types = get_entity_types(items)
        if entity_types:
            unions.append(Union("_Entity", entity_types))

        if scalars is None:
            scalars = []

        scalars.extend([_Any, FieldSet, LinkImport])

        items = GraphInit.init(items, is_async, bool(entity_types))

        super().__init__(
            items, data_types, directives, unions, interfaces, enums, scalars
        )
