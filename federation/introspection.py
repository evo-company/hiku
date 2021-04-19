from federation.directive import (
    KeyDirective,
    RequiresDirective,
    ProvidesDirective,
    ExternalDirective
)
from federation.graph import FederatedGraph
from hiku.graph import (
    Field,
    GraphTransformer,
    Option,
)
from hiku.introspection.graphql import (
    GraphQLIntrospection,
)
from hiku.types import (
    Sequence,
    Any,
)


class AddFederationFields(GraphTransformer):
    def visit_root(self, obj):
        root = super().visit_root(obj)
        root.fields.append(self.get_entities_field())
        return root

    def get_entities_field(self):
        # TODO _entities Sequence[Any] has to be Sequence[Union['_Entity']]
        return Field('_entities', Sequence[Any], lambda: None, options=[
            # TODO representations Sequence[Any] has to be Sequence['_Any']
            Option('representations', Sequence[Any])
        ])


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

        # query_graph = AddFederationFields().visit(query_graph)
        super().__init__(query_graph, mutation_graph, directives)

    def visit_graph(self, obj):
        graph = super().visit_graph(obj)
        graph = FederatedGraph(graph.items, data_types=graph.data_types)
        graph.extend_links = obj.extend_links
        graph.extend_nodes = obj.extend_nodes
        graph.extend_node_keys_map = obj.extend_node_keys_map
        return graph
