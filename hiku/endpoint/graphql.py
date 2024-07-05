import typing as t

from abc import ABC
from asyncio import gather


from hiku.schema import GraphQLError, GraphQLRequest, GraphQLResponse, Schema
from ..graph import Graph


BatchedRequest = t.List[GraphQLRequest]
BatchedResponse = t.List[GraphQLResponse]

SingleOrBatchedRequest = t.Union[GraphQLRequest, BatchedRequest]
SingleOrBatchedResponse = t.Union[GraphQLResponse, BatchedResponse]


# TODO: do we need it ?
G = t.TypeVar("G", bound=Graph)
C = t.TypeVar("C")


class BaseGraphQLEndpoint(ABC, t.Generic[C]):
    """TODO: add doc explaining the purpose of this class over plain schema"""

    schema: Schema

    def __init__(
        self,
        schema: Schema,
        batching: bool = False,
    ):
        self.schema = schema
        self.batching = batching


class BaseSyncGraphQLEndpoint(BaseGraphQLEndpoint):
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
        return self.schema.execute_sync(data, context)


class BaseAsyncGraphQLEndpoint(BaseGraphQLEndpoint):
    async def dispatch(
        self, data: GraphQLRequest, context: t.Optional[t.Dict] = None
    ) -> GraphQLResponse:
        # TODO: what it we want to override exception handling?
        return await self.schema.execute(data, context)


class GraphQLEndpoint(BaseSyncGraphQLEndpoint):
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
