from typing import (
    Callable,
    Optional,
)

from hiku.graph import Field, Graph
from hiku.introspection.graphql import GraphQLIntrospection
from hiku.introspection.graphql import AsyncGraphQLIntrospection


def _is_field_hidden_wrapper(func: Callable) -> Callable:
    def wrapper(field: Field) -> bool:
        if field.name in ("_entities", "_service"):
            return False

        return func(field)

    return wrapper


def _is_data_type_as_input_wrapper(func: Callable) -> Callable:
    def wrapper(name: str) -> bool:
        if name in ("_Service",):
            return False

        return func(name)

    return wrapper


class BaseFederatedGraphQLIntrospection(GraphQLIntrospection):
    def __init__(
        self,
        query_graph: Graph,
        mutation_graph: Optional[Graph] = None,
    ) -> None:
        super().__init__(query_graph, mutation_graph)
        self.schema.is_field_hidden = _is_field_hidden_wrapper(  # type: ignore
            self.schema.is_field_hidden
        )
        self.schema.is_data_type_as_input = _is_data_type_as_input_wrapper(  # type: ignore  # noqa: E501
            self.schema.is_data_type_as_input
        )


class FederatedGraphQLIntrospection(BaseFederatedGraphQLIntrospection):
    """
    Federation-aware introspection for Federation
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection, AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
