import typing as t

from abc import ABC, abstractmethod
from asyncio import gather
from inspect import isawaitable

from ..engine import Engine
from ..extentions.runner import ExtensionsRunner
from ..extentions.context import ExecutionContext
from ..graph import (
    apply,
    Graph,
)
from ..query import (
    QueryTransformer,
    Node,
)
from ..result import Proxy
from ..validate.query import validate
from ..readers.graphql import (
    read_operation,
    OperationType,
    Operation,
)
from ..denormalize.graphql import DenormalizeGraphQL
from ..introspection.graphql import AsyncGraphQLIntrospection, QUERY_ROOT_NAME
from ..introspection.graphql import GraphQLIntrospection, MUTATION_ROOT_NAME


_type_names: t.Dict[OperationType, str] = {
    OperationType.QUERY: QUERY_ROOT_NAME,
    OperationType.MUTATION: MUTATION_ROOT_NAME,
}


class GraphQLError(Exception):

    def __init__(self, *, errors: t.List[str]):
        super().__init__('{} errors'.format(len(errors)))
        self.errors = errors


class _StripQuery(QueryTransformer):
    """Removes __typename fields from query"""

    def visit_node(self, obj: Node) -> Node:
        return obj.copy(fields=[self.visit(f) for f in obj.fields
                                if f.name != '__typename'])


def _switch_graph(
    execution_context: ExecutionContext,
    extensions_runner: ExtensionsRunner,
) -> t.Tuple[Graph, Operation]:
    try:
        op = read_operation(execution_context,
                            extensions_runner)
    except TypeError as e:
        raise GraphQLError(errors=[
            'Failed to read query: {}'.format(e),
        ])
    if op.type is OperationType.QUERY:
        graph = execution_context.query_graph
    elif op.type is OperationType.MUTATION and execution_context.mutation_graph is not None:
        graph = execution_context.mutation_graph
    else:
        raise GraphQLError(errors=[
            'Unsupported operation type: {!r}'.format(op.type),
        ])
    return graph, op


def _process_query(graph: Graph, query: Node) -> Node:
    stripped_query = _StripQuery().visit(query)
    errors = validate(graph, stripped_query)
    if errors:
        raise GraphQLError(errors=errors)
    else:
        return stripped_query


class BaseGraphQLEndpoint(ABC):
    query_graph: Graph
    mutation_graph: t.Optional[Graph]

    @property
    @abstractmethod
    def introspection_cls(self) -> t.Type[GraphQLIntrospection]:
        pass

    def __init__(
        self,
        engine: Engine,
        query_graph: Graph,
        mutation_graph: t.Optional[Graph] = None,
        extensions: t.Optional[t.List] = None,
    ):
        self.engine = engine
        self.extensions = extensions or []

        introspection = self.introspection_cls(query_graph, mutation_graph)
        self.query_graph = apply(query_graph, [introspection])
        if mutation_graph is not None:
            self.mutation_graph = apply(mutation_graph, [introspection])
        else:
            self.mutation_graph = None


class BaseSyncGraphQLEndpoint(BaseGraphQLEndpoint):
    @abstractmethod
    def execute(self, graph: Graph, op: Operation, ctx: t.Dict) -> t.Dict:
        pass

    @abstractmethod
    def dispatch(self, data: t.Dict) -> t.Dict:
        pass


class BaseAsyncGraphQLEndpoint(BaseGraphQLEndpoint):
    @abstractmethod
    async def execute(self, graph: Graph, op: Operation, ctx: t.Dict) -> t.Dict:
        pass

    @abstractmethod
    async def dispatch(self, data: t.Dict) -> t.Dict:
        pass


class GraphQLEndpoint(BaseSyncGraphQLEndpoint):
    introspection_cls = GraphQLIntrospection

    def execute(
        self, graph: Graph, op: Operation, ctx: t.Optional[t.Dict]
    ) -> t.Dict:
        stripped_query = _process_query(graph, op.query)
        result = self.engine.execute(graph, stripped_query, ctx, op)
        assert isinstance(result, Proxy)
        type_name = _type_names[op.type]
        return DenormalizeGraphQL(graph, result, type_name).process(op.query)

    def dispatch(self, data: t.Dict) -> t.Dict:
        execution_context = ExecutionContext(
            query=data['query'],
            variables=data.get('variables'),
            operation_name=data.get('operationName'),
            query_graph=self.query_graph,
            mutation_graph=self.mutation_graph,
        )
        extensions_runner = ExtensionsRunner(
            execution_context,
            self.extensions
        )
        try:
            graph, op = _switch_graph(
                execution_context,
                extensions_runner
            )
            result = self.execute(graph, op, {})
            return {'data': result}
        except GraphQLError as e:
            return {'errors': [{'message': e} for e in e.errors]}


class BatchGraphQLEndpoint(GraphQLEndpoint):

    @t.overload
    def dispatch(self, data: t.List[t.Dict]) -> t.List[t.Dict]:
        ...

    @t.overload
    def dispatch(self, data: t.Dict) -> t.Dict:
        ...

    def dispatch(
        self, data: t.Union[t.Dict, t.List[t.Dict]]
    ) -> t.Union[t.Dict, t.List[t.Dict]]:
        if isinstance(data, list):
            return [
                super(BatchGraphQLEndpoint, self).dispatch(item)
                for item in data
            ]
        else:
            return super(BatchGraphQLEndpoint, self).dispatch(data)


class AsyncGraphQLEndpoint(BaseAsyncGraphQLEndpoint):
    introspection_cls = AsyncGraphQLIntrospection

    async def execute(
        self, graph: Graph, op: Operation, ctx: t.Optional[t.Dict]
    ) -> t.Dict:
        stripped_query = _process_query(graph, op.query)
        coro = self.engine.execute(graph, stripped_query, ctx, op)
        assert isawaitable(coro)
        result = await coro
        type_name = _type_names[op.type]
        return DenormalizeGraphQL(graph, result, type_name).process(op.query)

    async def dispatch(self, data: t.Dict) -> t.Dict:
        try:
            graph, op = _switch_graph(
                data, self.query_graph, self.mutation_graph,
            )
            result = await self.execute(graph, op, {})
            return {'data': result}
        except GraphQLError as e:
            return {'errors': [{'message': e} for e in e.errors]}


class AsyncBatchGraphQLEndpoint(AsyncGraphQLEndpoint):

    @t.overload
    async def dispatch(self, data: t.List[t.Dict]) -> t.List[t.Dict]:
        ...

    @t.overload
    async def dispatch(self, data: t.Dict) -> t.Dict:
        ...

    async def dispatch(
        self, data: t.Union[t.Dict, t.List[t.Dict]]
    ) -> t.Union[t.Dict, t.List[t.Dict]]:
        if isinstance(data, list):
            return list(await gather(*(
                super(AsyncBatchGraphQLEndpoint, self).dispatch(item)
                for item in data
            )))
        else:
            return await super(AsyncBatchGraphQLEndpoint, self).dispatch(data)
