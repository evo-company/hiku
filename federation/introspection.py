from federation.directive import (
    KeyDirective,
    RequiresDirective,
    ProvidesDirective,
    ExternalDirective
)
from hiku.introspection.graphql import (
    GraphQLIntrospection,
    AsyncGraphQLIntrospection,
)
from hiku.introspection.types import SCALAR


class FederatedGraphQLIntrospection(GraphQLIntrospection):
    """
    Federation-aware introspection
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """
    def __init__(self, query_graph, mutation_graph=None, directives=None, scalars=None):
        if not directives:
            directives = []

        directives.extend([
            KeyDirective(),
            RequiresDirective(),
            ProvidesDirective(),
            ExternalDirective()
        ])

        if not scalars:
            scalars = []

        scalars.extend([
            SCALAR('_Any'),
        ])

        super().__init__(query_graph, mutation_graph, directives, scalars)

    def visit_graph(self, obj):
        """TODO this visit method converts FederatedGraph back to Graph"""
        return super().visit_graph(obj)


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection,
    AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
