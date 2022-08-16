import abc
from .engine import Engine as Engine
from .introspection import AsyncFederatedGraphQLIntrospection as AsyncFederatedGraphQLIntrospection, FederatedGraphQLIntrospection as FederatedGraphQLIntrospection, extend_with_federation as extend_with_federation, is_introspection_query as is_introspection_query
from .utils import get_keys as get_keys
from .validate import validate as validate
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from hiku.denormalize.graphql import DenormalizeGraphQL as DenormalizeGraphQL
from hiku.endpoint.graphql import GraphQLError as GraphQLError
from hiku.federation.denormalize import DenormalizeEntityGraphQL as DenormalizeEntityGraphQL
from hiku.graph import Graph as Graph, apply as apply
from hiku.query import Node as Node
from hiku.readers.graphql import Operation as Operation
from hiku.result import Proxy as Proxy, Reference as Reference
from typing import Any, Dict, Iterator, List, Optional, Type, overload

def denormalize_entities(graph: Graph, query: Node, result: Proxy) -> List[Dict[str, Any]]: ...

class BaseFederatedGraphEndpoint(ABC, metaclass=abc.ABCMeta):
    query_graph: Graph
    mutation_graph: Optional[Graph]
    @property
    @abstractmethod
    def introspection_cls(self) -> Type[FederatedGraphQLIntrospection]: ...
    engine: Incomplete
    def __init__(self, engine: Engine, query_graph: Graph, mutation_graph: Optional[Graph] = ...) -> None: ...
    def context(self, op: Operation) -> Iterator[Dict]: ...
    @staticmethod
    def postprocess_result(result: Proxy, graph: Graph, op: Operation) -> Dict: ...

class BaseSyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint, metaclass=abc.ABCMeta):
    @abstractmethod
    def execute(self, graph: Graph, op: Operation, ctx: Dict) -> Dict: ...
    @abstractmethod
    def dispatch(self, data: Dict) -> Dict: ...

class BaseAsyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint, metaclass=abc.ABCMeta):
    @abstractmethod
    async def execute(self, graph: Graph, op: Operation, ctx: Dict) -> Dict: ...
    @abstractmethod
    async def dispatch(self, data: Dict) -> Dict: ...

class FederatedGraphQLEndpoint(BaseSyncFederatedGraphQLEndpoint):
    introspection_cls: Incomplete
    def execute(self, graph: Graph, op: Operation, ctx: Optional[Dict]) -> Dict: ...
    def dispatch(self, data: Dict) -> Dict: ...

class AsyncFederatedGraphQLEndpoint(BaseAsyncFederatedGraphQLEndpoint):
    introspection_cls: Incomplete
    async def execute(self, graph: Graph, op: Operation, ctx: Optional[Dict]) -> Dict: ...
    async def dispatch(self, data: Dict) -> Dict: ...

class AsyncBatchFederatedGraphQLEndpoint(AsyncFederatedGraphQLEndpoint):
    @overload
    async def dispatch(self, data: List[Dict]) -> List[Dict]: ...
    @overload
    async def dispatch(self, data: Dict) -> Dict: ...
