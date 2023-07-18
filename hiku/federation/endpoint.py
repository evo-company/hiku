from abc import (
    ABC,
    abstractmethod,
)
from asyncio import gather
from contextlib import contextmanager
from inspect import isawaitable
from typing import (
    List,
    Dict,
    Any,
    Optional,
    overload,
    Iterator,
    Union,
    Type,
)

from hiku.federation.engine import Engine
from hiku.federation.introspection import (
    BaseFederatedGraphQLIntrospection,
    FederatedGraphQLIntrospection,
    AsyncFederatedGraphQLIntrospection,
)
from hiku.federation.validate import validate

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.federation.denormalize import DenormalizeEntityGraphQL
from hiku.endpoint.graphql import (
    _type_names,
    _switch_graph,
    GraphQLError,
    _StripQuery,
)
from hiku.graph import (
    Graph,
    apply,
)
from hiku.query import Node
from hiku.result import Proxy
from hiku.readers.graphql import Operation


def _process_query(graph: Graph, query: Node) -> Node:
    stripped_query = _StripQuery().visit(query)
    errors = validate(graph, stripped_query)
    if errors:
        raise GraphQLError(errors=errors)
    else:
        return stripped_query


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


class BaseFederatedGraphEndpoint(ABC):
    query_graph: Graph
    mutation_graph: Optional[Graph]

    @property
    @abstractmethod
    def introspection_cls(self) -> Type[BaseFederatedGraphQLIntrospection]:
        pass

    def __init__(
        self,
        engine: Engine,
        query_graph: Graph,
        mutation_graph: Optional[Graph] = None,
    ):
        self.engine = engine

        introspection = self.introspection_cls(query_graph, mutation_graph)
        self.query_graph = apply(query_graph, [introspection])
        if mutation_graph is not None:
            self.mutation_graph = apply(mutation_graph, [introspection])
        else:
            self.mutation_graph = None

    @contextmanager
    def context(self, op: Operation) -> Iterator[Dict]:
        yield {}

    def postprocess_result(
        self, result: Proxy, graph: Graph, op: Operation
    ) -> Dict:
        if "_service" in op.query.fields_map:
            return {"_service": {"sdl": result["sdl"]}}

        type_name = _type_names[op.type]

        data = DenormalizeGraphQL(graph, result, type_name).process(op.query)
        return data


class BaseSyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    @abstractmethod
    def execute(self, graph: Graph, op: Operation, ctx: Dict) -> Dict:
        pass

    @abstractmethod
    def dispatch(self, data: Dict) -> Dict:
        pass


class BaseAsyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    @abstractmethod
    async def execute(self, graph: Graph, op: Operation, ctx: Dict) -> Dict:
        pass

    @abstractmethod
    async def dispatch(self, data: Dict) -> Dict:
        pass


class FederatedGraphQLEndpoint(BaseSyncFederatedGraphQLEndpoint):
    """Can execute either regular or federated queries.
    Handles following fields of federated query:
        - _service
        - _entities
    """

    @property
    def introspection_cls(self) -> Type[BaseFederatedGraphQLIntrospection]:
        return FederatedGraphQLIntrospection

    def execute(self, graph: Graph, op: Operation, ctx: Optional[Dict]) -> Dict:
        stripped_query = _process_query(graph, op.query)
        if "_service" in stripped_query.fields_map:
            result = self.engine.execute_service(graph, self.mutation_graph)
        else:
            result = self.engine.execute(graph, stripped_query, ctx or {}, op)

        assert isinstance(result, Proxy)
        return self.postprocess_result(result, graph, op)

    def dispatch(self, data: Dict) -> Dict:
        try:
            graph, op = _switch_graph(
                data,
                self.query_graph,
                self.mutation_graph,
            )
            with self.context(op) as ctx:
                result = self.execute(graph, op, ctx)
            return {"data": result}
        except GraphQLError as e:
            return {"errors": [{"message": e} for e in e.errors]}


class AsyncFederatedGraphQLEndpoint(BaseAsyncFederatedGraphQLEndpoint):
    @property
    def introspection_cls(self) -> Type[BaseFederatedGraphQLIntrospection]:
        return AsyncFederatedGraphQLIntrospection

    async def execute(
        self, graph: Graph, op: Operation, ctx: Optional[Dict]
    ) -> Dict:
        stripped_query = _process_query(graph, op.query)
        if "_service" in stripped_query.fields_map:
            coro = self.engine.execute_service(graph, self.mutation_graph)
        else:
            coro = self.engine.execute(graph, stripped_query, ctx)

        assert isawaitable(coro)
        result = await coro
        return self.postprocess_result(result, graph, op)

    async def dispatch(self, data: Dict) -> Dict:
        try:
            graph, op = _switch_graph(
                data,
                self.query_graph,
                self.mutation_graph,
            )

            with self.context(op) as ctx:
                result = await self.execute(graph, op, ctx)
            return {"data": result}
        except GraphQLError as e:
            return {"errors": [{"message": e} for e in e.errors]}


class AsyncBatchFederatedGraphQLEndpoint(AsyncFederatedGraphQLEndpoint):
    @overload
    async def dispatch(self, data: List[Dict]) -> List[Dict]:
        ...

    @overload
    async def dispatch(self, data: Dict) -> Dict:
        ...

    async def dispatch(
        self, data: Union[Dict, List[Dict]]
    ) -> Union[Dict, List[Dict]]:
        if isinstance(data, list):
            return list(
                await gather(*(super().dispatch(item) for item in data))
            )

        return await super().dispatch(data)
