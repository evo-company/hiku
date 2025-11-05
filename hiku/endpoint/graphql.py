from typing import Any, overload, TypedDict

from abc import ABC
from asyncio import gather

from hiku.error import GraphQLError
from hiku.schema import ExecutionResult, Schema


class GraphQLErrorObject(TypedDict):
    message: str


class GraphQLRequest(TypedDict, total=False):
    query: str
    variables: dict[str, Any] | None
    operationName: str | None


class GraphQLResponse(TypedDict, total=False):
    data: dict[str, object] | None
    errors: list[GraphQLErrorObject] | None
    extensions: dict[str, object] | None


BatchedRequest = list[GraphQLRequest]
BatchedResponse = list[GraphQLResponse]

SingleOrBatchedRequest = GraphQLRequest | BatchedRequest
SingleOrBatchedResponse = GraphQLResponse | BatchedResponse


class BaseGraphQLEndpoint(ABC):
    """TODO: add doc explaining the purpose of this class over plain schema"""

    schema: Schema

    def __init__(
        self,
        schema: Schema,
        batching: bool = False,
    ):
        self.schema = schema
        self.batching = batching

    def process_result(self, result: ExecutionResult) -> GraphQLResponse:
        data: GraphQLResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [{"message": e.message} for e in result.errors]

        return data


class BaseSyncGraphQLEndpoint(BaseGraphQLEndpoint):
    def dispatch(
        self, data: GraphQLRequest, context: dict[str, Any] | None = None
    ) -> GraphQLResponse:
        """
        Dispatch graphql request to graph

        Example:

        .. code-block:: python

            result = endpoint.dispatch({"query": "{ hello }"})

        :param dict data:
            {"query": str, "variables": dict, "operationName": str}
        :param dict context: context for operation
        :return: :py:class:`dict` graphql response: data or errors
        """
        assert "query" in data, "query is required"
        result = self.schema.execute_sync(
            query=data["query"],
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
            context=context,
        )
        return self.process_result(result)


class BaseAsyncGraphQLEndpoint(BaseGraphQLEndpoint):
    async def dispatch(
        self, data: GraphQLRequest, context: dict[str, Any] | None = None
    ) -> GraphQLResponse:
        """Dispatch graphql request to graph

        Example:

        .. code-block:: python

            result = await endpoint.dispatch({"query": "{ hello }"})

        :param dict data:
            {"query": str, "variables": dict, "operationName": str}
        :param dict context: context for operation
        :return: :py:class:`dict` graphql response: data or errors
        """
        assert "query" in data, "query is required"
        result = await self.schema.execute(
            query=data["query"],
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
            context=context,
        )
        return self.process_result(result)


class GraphQLEndpoint(BaseSyncGraphQLEndpoint):
    @overload
    def dispatch(
        self, data: GraphQLRequest, context: dict[str, Any] | None = None
    ) -> GraphQLResponse: ...

    @overload
    def dispatch(
        self, data: BatchedRequest, context: dict[str, Any] | None = None
    ) -> BatchedResponse: ...

    def dispatch(
        self,
        data: SingleOrBatchedRequest,
        context: dict[str, Any] | None = None,
    ) -> SingleOrBatchedResponse:
        if isinstance(data, list):
            if not self.batching:
                raise GraphQLError("Batching is not supported")

            return [
                super(GraphQLEndpoint, self).dispatch(item, context)
                for item in data
            ]
        else:
            return super(GraphQLEndpoint, self).dispatch(data, context)


class BatchGraphQLEndpoint(GraphQLEndpoint):
    """For backward compatibility"""

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["batching"] = True
        super().__init__(*args, **kwargs)


class AsyncGraphQLEndpoint(BaseAsyncGraphQLEndpoint):
    @overload
    async def dispatch(
        self, data: GraphQLRequest, context: dict[str, Any] | None = None
    ) -> GraphQLResponse: ...

    @overload
    async def dispatch(
        self, data: BatchedRequest, context: dict[str, Any] | None = None
    ) -> BatchedResponse: ...

    async def dispatch(
        self,
        data: SingleOrBatchedRequest,
        context: dict[str, Any] | None = None,
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

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs["batching"] = True
        super().__init__(*args, **kwargs)
