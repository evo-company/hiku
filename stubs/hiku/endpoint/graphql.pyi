import abc
import typing as t
from ..denormalize.graphql import DenormalizeGraphQL as DenormalizeGraphQL
from ..engine import Engine as Engine
from ..graph import Graph as Graph, apply as apply
from ..introspection.graphql import AsyncGraphQLIntrospection as AsyncGraphQLIntrospection, GraphQLIntrospection as GraphQLIntrospection, MUTATION_ROOT_NAME as MUTATION_ROOT_NAME, QUERY_ROOT_NAME as QUERY_ROOT_NAME
from ..query import Node as Node, QueryTransformer as QueryTransformer
from ..readers.graphql import Operation as Operation, OperationType as OperationType, read_operation as read_operation
from ..result import Proxy as Proxy
from ..validate.query import validate as validate
from _typeshed import Incomplete
from abc import ABC, abstractmethod

class GraphQLError(Exception):
    errors: Incomplete
    def __init__(self, *, errors: t.List[str]) -> None: ...

class _StripQuery(QueryTransformer):
    def visit_node(self, obj: Node) -> Node: ...

class BaseGraphQLEndpoint(ABC, metaclass=abc.ABCMeta):
    query_graph: Graph
    mutation_graph: t.Optional[Graph]
    @property
    @abstractmethod
    def introspection_cls(self) -> t.Type[GraphQLIntrospection]: ...
    engine: Incomplete
    def __init__(self, engine: Engine, query_graph: Graph, mutation_graph: t.Optional[Graph] = ...) -> None: ...

class BaseSyncGraphQLEndpoint(BaseGraphQLEndpoint, metaclass=abc.ABCMeta):
    @abstractmethod
    def execute(self, graph: Graph, op: Operation, ctx: t.Dict) -> t.Dict: ...
    @abstractmethod
    def dispatch(self, data: t.Dict) -> t.Dict: ...

class BaseAsyncGraphQLEndpoint(BaseGraphQLEndpoint, metaclass=abc.ABCMeta):
    @abstractmethod
    async def execute(self, graph: Graph, op: Operation, ctx: t.Dict) -> t.Dict: ...
    @abstractmethod
    async def dispatch(self, data: t.Dict) -> t.Dict: ...

class GraphQLEndpoint(BaseSyncGraphQLEndpoint):
    introspection_cls: Incomplete
    def execute(self, graph: Graph, op: Operation, ctx: t.Optional[t.Dict]) -> t.Dict: ...
    def dispatch(self, data: t.Dict) -> t.Dict: ...

class BatchGraphQLEndpoint(GraphQLEndpoint):
    @t.overload
    def dispatch(self, data: t.List[t.Dict]) -> t.List[t.Dict]: ...
    @t.overload
    def dispatch(self, data: t.Dict) -> t.Dict: ...

class AsyncGraphQLEndpoint(BaseAsyncGraphQLEndpoint):
    introspection_cls: Incomplete
    async def execute(self, graph: Graph, op: Operation, ctx: t.Optional[t.Dict]) -> t.Dict: ...
    async def dispatch(self, data: t.Dict) -> t.Dict: ...

class AsyncBatchGraphQLEndpoint(AsyncGraphQLEndpoint):
    @t.overload
    async def dispatch(self, data: t.List[t.Dict]) -> t.List[t.Dict]: ...
    @t.overload
    async def dispatch(self, data: t.Dict) -> t.Dict: ...
