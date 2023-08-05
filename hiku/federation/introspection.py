from typing import (
    Callable,
    Optional,
)

from hiku.graph import Field, Graph, Link, Node
from hiku.types import String, TypeRef
from hiku.introspection.graphql import GraphQLIntrospection
from hiku.introspection.graphql import AsyncGraphQLIntrospection


def _is_field_hidden_wrapper(func: Callable) -> Callable:
    def wrapper(field: Field) -> bool:
        if field.name in ("_entities", "_service"):
            return False

        return func(field)

    return wrapper


class BaseFederatedGraphQLIntrospection(GraphQLIntrospection):
    def __init__(
        self,
        query_graph: Graph,
        mutation_graph: Optional[Graph] = None,
    ) -> None:
        super().__init__(query_graph, mutation_graph)
        self.schema.nodes_map["_Service"] = Node(
            "_Service", [Field("sdl", String, lambda: None)]  # type: ignore
        )
        self.schema.is_field_hidden = _is_field_hidden_wrapper(  # type: ignore
            self.schema.is_field_hidden
        )
        self.schema.nodes_map["Query"] = self.schema.nodes_map["Query"].copy()
        self.schema.nodes_map["Query"].fields.append(
            Link("_service", TypeRef["_Service"], lambda: None, requires=None)
        )


class FederatedGraphQLIntrospection(BaseFederatedGraphQLIntrospection):
    """
    Federation-aware introspection for Federation
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """

    __directives__ = GraphQLIntrospection.__directives__


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection, AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
