from ..graph import Graph as Graph
from ..introspection.graphql import AsyncGraphQLIntrospection as AsyncGraphQLIntrospection, Directive as Directive, GraphQLIntrospection as GraphQLIntrospection
from ..introspection.types import NON_NULL as NON_NULL, SCALAR as SCALAR
from ..query import Node as QueryNode
from .utils import get_keys as get_keys
from _typeshed import Incomplete

def is_introspection_query(query: QueryNode) -> bool: ...
def extend_with_federation(graph: Graph, data: dict) -> None: ...

class FederatedGraphQLIntrospection(GraphQLIntrospection):
    __directives__: Incomplete

class AsyncFederatedGraphQLIntrospection(FederatedGraphQLIntrospection, AsyncGraphQLIntrospection): ...
