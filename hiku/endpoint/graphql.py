import typing as t

from abc import ABC, abstractmethod
from asyncio import gather

from typing_extensions import TypedDict

from hiku.merge import QueryMerger
from hiku.graph import GraphTransformer

from hiku.result import Proxy

from ..context import (
    ExecutionContextFinal,
    create_execution_context,
    ExecutionContext,
)
from ..engine import Engine
from ..extensions.base_extension import Extension, ExtensionsManager
from ..extensions.base_validator import QueryValidator
from ..graph import apply, Graph
from ..operation import OperationType
from ..query import Node
from ..validate.query import validate
from ..readers.graphql import (
    parse_query,
    read_operation,
)
from ..denormalize.graphql import DenormalizeGraphQL
from ..introspection.graphql import AsyncGraphQLIntrospection
from ..introspection.graphql import GraphQLIntrospection


class GraphQLErrorObject(TypedDict):
    message: str


class GraphQLRequest(TypedDict, total=False):
    query: str
    variables: t.Optional[t.Dict[t.Any, t.Any]]
    operationName: t.Optional[str]


class GraphQLResponseError(TypedDict):
    errors: t.List[GraphQLErrorObject]


class GraphQLResponseOk(TypedDict):
    data: t.Dict[t.Any, t.Any]


GraphQLResponse = t.Union[GraphQLResponseError, GraphQLResponseOk]

BatchedRequest = t.List[GraphQLRequest]
BatchedResponse = t.List[GraphQLResponse]

SingleOrBatchedRequest = t.Union[GraphQLRequest, BatchedRequest]
SingleOrBatchedResponse = t.Union[GraphQLResponse, BatchedResponse]


class GraphQLError(Exception):
    def __init__(self, *, errors: t.List[str]):
        super().__init__("{} errors".format(len(errors)))
        self.errors = errors


G = t.TypeVar("G", bound=Graph)


def _run_validation(
    graph: Graph,
    query: Node,
    validators: t.Optional[t.Tuple[QueryValidator, ...]] = None,
) -> t.List[str]:
    errors = validate(graph, query)
    for validator in validators or ():
        errors.extend(validator.validate(query, graph))

    return errors


C = t.TypeVar("C")


class BaseGraphQLEndpoint(ABC, t.Generic[C]):
    query_graph: Graph
    mutation_graph: t.Optional[Graph]
    batching: bool
    validation: bool
    introspection: bool

    @property
    @abstractmethod
    def introspection_cls(self) -> t.Type[GraphQLIntrospection]:
        pass

    def __init__(
        self,
        engine: Engine,
        query_graph: Graph,
        mutation_graph: t.Optional[Graph] = None,
        batching: bool = False,
        validation: bool = True,
        introspection: bool = True,
        extensions: t.Optional[
            t.Sequence[t.Union[Extension, t.Type[Extension]]]
        ] = None,
    ):
        self.engine = engine
        self.batching = batching
        self.validation = validation
        self.introspection = introspection
        self.extensions = extensions or []

        execution_context = create_execution_context()
        extensions_manager = ExtensionsManager(
            execution_context=execution_context,
            extensions=self.extensions,
        )
        with extensions_manager.graph():
            transformers: t.List[GraphTransformer] = list(
                execution_context.transformers
            )

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
        graph: Graph,
        query: Node,
        validators: t.Optional[t.Tuple[QueryValidator, ...]] = None,
    ) -> t.List[str]:
        return _run_validation(graph, query, validators)

    def _init_execution_context(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> None:
        with extensions_manager.parsing():
            if execution_context.graphql_document is None:
                execution_context.graphql_document = parse_query(
                    execution_context.query_src
                )

        with extensions_manager.operation():
            if execution_context.operation is None:
                try:
                    execution_context.operation = read_operation(
                        execution_context.graphql_document,
                        execution_context.variables,
                        execution_context.request_operation_name,
                    )
                except TypeError as e:
                    raise GraphQLError(
                        errors=[
                            "Failed to read query: {}".format(e),
                        ]
                    )

            execution_context.query = execution_context.operation.query

            with extensions_manager.validation():
                if self.validation and execution_context.errors is None:
                    execution_context.errors = self._validate(
                        execution_context.graph,
                        execution_context.query,
                        execution_context.validators,
                    )

            if execution_context.errors:
                raise GraphQLError(errors=execution_context.errors)

            merger = QueryMerger(execution_context.graph)
            execution_context.query = merger.merge(execution_context.query)

        op = execution_context.operation
        if op.type not in (OperationType.QUERY, OperationType.MUTATION):
            raise GraphQLError(
                errors=["Unsupported operation type: {!r}".format(op.type)]
            )


class BaseSyncGraphQLEndpoint(BaseGraphQLEndpoint):
    @abstractmethod
    def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> t.Dict:
        pass

    def dispatch(
        self, data: GraphQLRequest, context: t.Optional[t.Dict] = None
    ) -> GraphQLResponse:
        """
        Dispatch graphql request to graph
        Args:
            data: {"query": str, "variables": dict, "operationName": str}
            context: context for operation

        Returns: graphql response: data or errors
        """
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


class BaseAsyncGraphQLEndpoint(BaseGraphQLEndpoint):
    @abstractmethod
    async def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> t.Dict:
        pass

    async def dispatch(
        self, data: GraphQLRequest, context: t.Optional[t.Dict] = None
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


class GraphQLEndpoint(BaseSyncGraphQLEndpoint):
    introspection_cls = GraphQLIntrospection

    def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> t.Dict:
        execution_context = t.cast(ExecutionContextFinal, execution_context)

        with extensions_manager.execution():
            result = self.engine.execute_context(execution_context)
            assert isinstance(result, Proxy)
            execution_context.result = result

        return DenormalizeGraphQL(
            execution_context.graph,
            result,
            execution_context.operation_type_name,
        ).process(execution_context.query)

    @t.overload
    def dispatch(
        self, data: GraphQLRequest, context: t.Optional[t.Dict] = None
    ) -> GraphQLResponse:
        ...

    @t.overload
    def dispatch(
        self, data: BatchedRequest, context: t.Optional[t.Dict] = None
    ) -> BatchedResponse:
        ...

    def dispatch(
        self, data: SingleOrBatchedRequest, context: t.Optional[t.Dict] = None
    ) -> SingleOrBatchedResponse:
        if isinstance(data, list):
            if not self.batching:
                raise GraphQLError(errors=["Batching is not supported"])

            return [
                super(GraphQLEndpoint, self).dispatch(item, context)
                for item in data
            ]
        else:
            return super(GraphQLEndpoint, self).dispatch(data, context)


class BatchGraphQLEndpoint(GraphQLEndpoint):
    """For backward compatibility"""

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        kwargs["batching"] = True
        super().__init__(*args, **kwargs)


class AsyncGraphQLEndpoint(BaseAsyncGraphQLEndpoint):
    introspection_cls = AsyncGraphQLIntrospection

    async def execute(
        self,
        execution_context: ExecutionContext,
        extensions_manager: ExtensionsManager,
    ) -> t.Dict:
        execution_context = t.cast(ExecutionContextFinal, execution_context)

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
            result = await self.engine.execute_context(execution_context)  # type: ignore[union-attr]  # noqa: E501
            execution_context.result = result

        return DenormalizeGraphQL(
            execution_context.graph,
            result,
            execution_context.operation_type_name,
        ).process(execution_context.query)

    @t.overload
    async def dispatch(
        self, data: GraphQLRequest, context: t.Optional[t.Dict] = None
    ) -> GraphQLResponse:
        ...

    @t.overload
    async def dispatch(
        self, data: BatchedRequest, context: t.Optional[t.Dict] = None
    ) -> BatchedResponse:
        ...

    async def dispatch(
        self, data: SingleOrBatchedRequest, context: t.Optional[t.Dict] = None
    ) -> SingleOrBatchedResponse:
        if isinstance(data, list):
            return list(
                await gather(
                    *(
                        super(AsyncGraphQLEndpoint, self).dispatch(
                            item, context
                        )
                        for item in data
                    )
                )
            )
        else:
            return await super(AsyncGraphQLEndpoint, self).dispatch(
                data, context
            )


class AsyncBatchGraphQLEndpoint(AsyncGraphQLEndpoint):
    """For backward compatibility"""

    def __init__(self, *args: t.Any, **kwargs: t.Any):
        kwargs["batching"] = True
        super().__init__(*args, **kwargs)
