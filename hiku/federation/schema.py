from typing import Generic, List, Optional, Sequence, Type, Union, cast
from hiku.cache import CacheSettings
from hiku.context import ExecutionContext, ExecutionContextFinal
from hiku.engine import _ExecutorType
from hiku.federation.introspection import FederatedGraphQLIntrospection
from hiku.federation.sdl import print_sdl
from hiku.graph import GraphTransformer
from hiku.schema import Schema as BaseSchema
from hiku.extensions.base_extension import Extension, ExtensionsManager
from hiku.federation.graph import Graph
from hiku.federation.version import DEFAULT_FEDERATION_VERSION
from hiku.federation.utils import get_entity_types

from hiku.graph import (
    GraphTransformer,
    Union as GraphUnion,
)


class FederationV1EntityTransformer(GraphTransformer):
    def visit_graph(self, obj: Graph) -> Graph:  # type: ignore
        entities = get_entity_types(obj.nodes, federation_version=1)
        unions = []
        for u in obj.unions:
            if u.name == "_Entity" and entities:
                unions.append(GraphUnion("_Entity", entities))
            else:
                unions.append(u)

        return Graph(
            [self.visit(node) for node in obj.items],
            obj.data_types,
            obj.directives,
            unions,
            obj.interfaces,
            obj.enums,
            obj.scalars,
        )


class Schema(BaseSchema, Generic[_ExecutorType]):
    """Can execute either regular or federated queries.
    Handles following fields of federated query:
        - _service
        - _entities
    """

    graph: Graph
    introspection_cls = FederatedGraphQLIntrospection
    federation_version: int

    def __init__(
        self,
        executor: _ExecutorType,
        graph: Graph,
        mutation: Optional[Graph] = None,
        batching: bool = False,
        introspection: bool = True,
        extensions: Optional[
            Sequence[Union[Extension, Type[Extension]]]
        ] = None,
        cache: Optional[CacheSettings] = None,
        federation_version: int = DEFAULT_FEDERATION_VERSION,
    ):
        transformers: List[GraphTransformer] = []
        if federation_version == 1:
            transformers.append(FederationV1EntityTransformer())

        super().__init__(
            graph=graph,
            mutation=mutation,
            batching=batching,
            introspection=introspection,
            extensions=extensions,
            transformers=transformers,
            executor=executor,
            cache=cache,
        )
        self.federation_version = federation_version

    def _init_execution_context(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> None:
        super()._init_execution_context(execution_context, extensions_manager)
        execution_context = cast(ExecutionContextFinal, execution_context)

        if "_service" in execution_context.query.fields_map:
            execution_context.context["__sdl__"] = print_sdl(
                self.graph,
                self.mutation,
                self.federation_version,
            )
