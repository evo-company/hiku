from federation.directive import (
    KeyDirective,
    RequiresDirective,
    ProvidesDirective,
    ExternalDirective
)
from federation.graph import FederatedGraph
from hiku.introspection.graphql import (
    GraphQLIntrospection,
    ValidateGraph,
)


class FederatedGraphQLIntrospection(GraphQLIntrospection):
    def __init__(self, query_graph, mutation_graph=None, directives=None):
        if not directives:
            directives = []

        directives.extend([
            KeyDirective(),
            RequiresDirective(),
            ProvidesDirective(),
            ExternalDirective()
        ])
        super().__init__(query_graph, mutation_graph, directives)

    def visit_graph(self, obj):
        ValidateGraph.validate(obj)
        introspection_graph = self.__introspection_graph__()
        items = [self.visit(node) for node in obj.items]
        items.extend(introspection_graph.items)
        graph = FederatedGraph(items, data_types=obj.data_types)
        # TODO HACK
        graph.extend_links = obj.extend_links
        graph.extend_nodes = obj.extend_nodes
        graph.extend_node_keys_map = obj.extend_node_keys_map
        return graph
