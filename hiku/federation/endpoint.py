from abc import abstractmethod
from asyncio import gather
from inspect import isawaitable
from typing import (
    List,
    Dict,
    Any,
    Optional,
    Sequence,
    Tuple,
    cast,
    overload,
    Union,
    Type,
)

from hiku.context import (
    ExecutionContext,
    ExecutionContextFinal,
    create_execution_context,
)
from hiku.extensions.base_extension import Extension, ExtensionsManager
from hiku.extensions.base_validator import QueryValidator
from hiku.federation.utils import get_entity_types
from hiku.federation.version import DEFAULT_FEDERATION_VERSION

from hiku.federation.sdl import print_sdl

from hiku.federation.graph import Graph
from hiku.federation.engine import Engine
from hiku.federation.introspection import (
    BaseFederatedGraphQLIntrospection,
    FederatedGraphQLIntrospection,
    AsyncFederatedGraphQLIntrospection,
)

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.federation.denormalize import DenormalizeEntityGraphQL
from hiku.endpoint.graphql import (
    BaseGraphQLEndpoint,
    BatchedRequest,
    BatchedResponse,
    GraphQLError,
    GraphQLRequest,
    GraphQLResponse,
    SingleOrBatchedRequest,
    SingleOrBatchedResponse,
    _run_validation as _run_validation_base,
)
from hiku.graph import (
    GraphTransformer,
    apply,
    Union as GraphUnion,
    Graph as _Graph,
)
from hiku.query import Node
from hiku.result import Proxy


GraphT = Union[Graph, _Graph]


def _run_validation(
    graph: GraphT,
    query: Node,
    validators: Optional[Tuple[QueryValidator, ...]] = None,
) -> List[str]:
    if "_entities" in query.fields_map or "_service" in query.fields_map:
        return []

    return _run_validation_base(graph, query, validators)


def denormalize_entities(
    graph: Graph,
    query: Node,
    result: Proxy,
) -> List[Dict[str, Any]]:
    representations = query.fields_map["_entities"].options["representations"]

    if not representations:
        return []

    typename = representations[0]["__typename"]
    data = DenormalizeEntityGraphQL(graph, result, typename).process(query)

    return data["_entities"]


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


class BaseFederatedGraphEndpoint(BaseGraphQLEndpoint):
    query_graph: Graph
    mutation_graph: Optional[Graph]
    engine: Engine
    batching: bool
    validation: bool
    introspection: bool
    federation_version: int

    @property
    @abstractmethod
    def introspection_cls(self) -> Type[BaseFederatedGraphQLIntrospection]:
        pass

    def __init__(
        self,
        engine: Engine,
        query_graph: Graph,
        mutation_graph: Optional[Graph] = None,
        batching: bool = False,
        validation: bool = True,
        introspection: bool = True,
        extensions: Optional[
            Sequence[Union[Extension, Type[Extension]]]
        ] = None,
        federation_version: int = DEFAULT_FEDERATION_VERSION,
    ):
        self.engine = engine
        self.federation_version = federation_version
        self.introspection = introspection
        self.batching = batching
        self.validation = validation
        self.extensions = extensions or []

        execution_context = create_execution_context()
        extensions_manager = ExtensionsManager(
            execution_context=execution_context,
            extensions=self.extensions,
        )
        with extensions_manager.graph():
            transformers: List[GraphTransformer] = list(
                execution_context.transformers
            )

        if federation_version == 1:
            transformers.append(FederationV1EntityTransformer())

        if self.introspection:
            transformers.append(
                self.introspection_cls(query_graph, mutation_graph)
            )

        self.query_graph = apply(query_graph, transformers)
        if mutation_graph is not None:
            self.mutation_graph = apply(mutation_graph, transformers)
        else:
            self.mutation_graph = None

    def _validate(
        self,
        graph: GraphT,
        query: Node,
        validators: Optional[Tuple[QueryValidator, ...]] = None,
    ) -> List[str]:
        return _run_validation(graph, query, validators)


class BaseSyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    @abstractmethod
    def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> Dict:
        pass

    def dispatch(self, data: Dict, context: Optional[Dict] = None) -> Dict:
        execution_context = create_execution_context(
            query=data["query"],
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
            context=context,
            query_graph=self.query_graph,
            mutation_graph=self.mutation_graph,
        )

        extensions_manager = ExtensionsManager(
            execution_context=execution_context,
            extensions=self.extensions,
        )

        try:
            with extensions_manager.dispatch():
                self._init_execution_context(
                    execution_context, extensions_manager
                )
                result = self.execute(execution_context, extensions_manager)
                return {"data": result}
        except GraphQLError as e:
            return {"errors": [{"message": e} for e in e.errors]}


class BaseAsyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    @abstractmethod
    async def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> Dict:
        pass

    async def dispatch(
        self, data: GraphQLRequest, context: Optional[Dict] = None
    ) -> GraphQLResponse:
        execution_context = create_execution_context(
            query=data["query"],
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
            context=context,
            query_graph=self.query_graph,
            mutation_graph=self.mutation_graph,
        )

        extensions_manager = ExtensionsManager(
            execution_context=execution_context,
            extensions=self.extensions,
        )

        try:
            with extensions_manager.dispatch():
                self._init_execution_context(
                    execution_context, extensions_manager
                )
                result = await self.execute(
                    execution_context, extensions_manager
                )
                return {"data": result}
        except GraphQLError as e:
            return {"errors": [{"message": e} for e in e.errors]}


class FederatedGraphQLEndpoint(BaseSyncFederatedGraphQLEndpoint):
    """Can execute either regular or federated queries.
    Handles following fields of federated query:
        - _service
        - _entities
    """

    @property
    def introspection_cls(self) -> Type[BaseFederatedGraphQLIntrospection]:
        return FederatedGraphQLIntrospection

    def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> Dict:
        execution_context = cast(ExecutionContextFinal, execution_context)

        with extensions_manager.execution():
            if "_service" in execution_context.query.fields_map:
                execution_context.context["__sdl__"] = print_sdl(
                    self.query_graph,
                    self.mutation_graph,
                    self.federation_version,
                )

            result = self.engine.execute_context(execution_context)
            assert isinstance(result, Proxy)
            execution_context.result = result

        return DenormalizeGraphQL(
            execution_context.graph,
            result,
            execution_context.operation_type_name,
        ).process(execution_context.query)

    def dispatch(self, data: Dict, context: Optional[Dict] = None) -> Dict:
        execution_context = create_execution_context(
            query=data["query"],
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
            context=context,
            query_graph=self.query_graph,
            mutation_graph=self.mutation_graph,
        )

        extensions_manager = ExtensionsManager(
            execution_context=execution_context,
            extensions=self.extensions,
        )

        try:
            with extensions_manager.dispatch():
                self._init_execution_context(
                    execution_context, extensions_manager
                )
                result = self.execute(execution_context, extensions_manager)
                return {"data": result}
        except GraphQLError as e:
            return {"errors": [{"message": e} for e in e.errors]}


class AsyncFederatedGraphQLEndpoint(BaseAsyncFederatedGraphQLEndpoint):
    @property
    def introspection_cls(self) -> Type[BaseFederatedGraphQLIntrospection]:
        return AsyncFederatedGraphQLIntrospection

    async def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> Dict:
        execution_context = cast(ExecutionContextFinal, execution_context)

        with extensions_manager.validation():
            if self.validation and execution_context.errors is None:
                execution_context.errors = _run_validation(
                    execution_context.graph,
                    execution_context.query,
                    execution_context.validators,
                )

        if execution_context.errors:
            raise GraphQLError(errors=execution_context.errors)

        with extensions_manager.execution():
            if "_service" in execution_context.query.fields_map:
                execution_context.context["__sdl__"] = print_sdl(
                    self.query_graph,
                    self.mutation_graph,
                    self.federation_version,
                )

            coro = self.engine.execute_context(execution_context)
            assert isawaitable(coro)
            result = await coro
            execution_context.result = result

        return DenormalizeGraphQL(
            execution_context.graph,
            result,
            execution_context.operation_type_name,
        ).process(execution_context.query)

    @overload
    async def dispatch(
        self, data: GraphQLRequest, context: Optional[Dict] = None
    ) -> GraphQLResponse:
        ...

    @overload
    async def dispatch(
        self, data: BatchedRequest, context: Optional[Dict] = None
    ) -> BatchedResponse:
        ...

    async def dispatch(
        self, data: SingleOrBatchedRequest, context: Optional[Dict] = None
    ) -> SingleOrBatchedResponse:
        if isinstance(data, list):
            return list(
                await gather(
                    *(super().dispatch(item, context) for item in data)
                )
            )

        return await super().dispatch(data, context)


class AsyncBatchFederatedGraphQLEndpoint(AsyncFederatedGraphQLEndpoint):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["batching"] = True
        super().__init__(*args, **kwargs)
