import typing as t
from inspect import isawaitable

from hiku.directives import SchemaDirective
from hiku.federation.utils import get_entity_types

from hiku.types import Any, Record, Sequence, TypeRef, Union

from hiku.graph import (
    Field,
    Graph as _Graph,
    GraphTransformer,
    Link,
    Node,
    Option,
    Root,
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

    @classmethod
    def init(
        cls, items: t.List[t.Union[FederatedNode, Node]], is_async: bool
    ) -> t.List[Node]:
        self = cls()
        self.type_to_resolve_reference_map = {}
        self.is_async = is_async
        return [self.visit(i) for i in items]

    def visit_root(self, root: Root) -> Root:
        return Root(root.fields + [self.entities_link()])

    def visit_node(self, obj: Node) -> Node:
        if hasattr(obj, "resolve_reference") and obj.name is not None:
            self.type_to_resolve_reference_map[obj.name] = obj.resolve_reference

        return super(GraphInit, self).visit_node(obj)

    def entities_link(self) -> Link:
        def entities_resolver(options: t.Dict) -> t.Tuple[t.List, str]:
            representations = options["representations"]
            if not representations:
                return [], ""

            typ = representations[0]["__typename"]

            if typ not in self.type_to_resolve_reference_map:
                raise TypeError(
                    'Type "{}" must have "reference_resolver"'.format(typ)
                )

            resolve_reference = self.type_to_resolve_reference_map[typ]
            return resolve_reference(representations), typ

        async def entities_resolver_async(
            options: t.Dict,
        ) -> t.Tuple[t.List, str]:
            representations = options["representations"]
            if not representations:
                return [], ""

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
                return await coro, typ

            return coro, typ

        return Link(
            "_entities",
            Sequence[TypeRef["_Entity"]],  # type: ignore
            entities_resolver_async if self.is_async else entities_resolver,
            options=[
                Option("representations", Sequence[Any]),
            ],
            requires=None,
        )


class Graph(_Graph):
    def __init__(
        self,
        items: t.List[t.Union[FederatedNode, Node]],
        data_types: t.Optional[t.Dict[str, t.Type[Record]]] = None,
        directives: t.Optional[t.Sequence[t.Type[SchemaDirective]]] = None,
        unions: t.Optional[t.List[t.Type[Union]]] = None,
        is_async: bool = False,
    ):
        items = GraphInit.init(items, is_async)
        if unions is None:
            unions = []

        entity_types = get_entity_types(items)
        unions.append(Union["_Entity", entity_types])
        super().__init__(items, data_types, directives, unions)
