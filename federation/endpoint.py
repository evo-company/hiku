from hiku.denormalize.graphql import (
    DenormalizeGraphQL,
)
from hiku.endpoint.graphql import (
    BaseGraphQLEndpoint,
    _process_query,
    _type_names,
    _switch_graph,
    GraphQLError,
)
from hiku.introspection.graphql import GraphQLIntrospection

from federation.graph import FederatedGraph


def denormalize(graph: FederatedGraph, query, result):
    entities_link = query.fields_map['_entities']
    representations = entities_link.options['representations']

    entities = []
    for rep in representations:
        typename = rep['__typename']

        data = result.__idx__[typename]
        keys = graph.extend_node_keys_map[typename]

        # TODO implement multiple keys like ['id', 'sku']
        entity = {}
        for key in keys:
            ident = rep[key]
            entity = data[ident]

        entities.append(entity)

    return entities


class FederatedGraphQLEndpoint(BaseGraphQLEndpoint):
    introspection_cls = GraphQLIntrospection

    def execute(self, graph, op, ctx):
        stripped_query = _process_query(graph, op.query)
        result = self.engine.execute(graph, stripped_query, ctx)
        type_name = _type_names[op.type]

        if '_entities' in op.query.fields_map:
            data = {'_entities': denormalize(graph, op.query, result)}
        else:
            data = DenormalizeGraphQL(graph, result, type_name).process(op.query)
        return data

    def dispatch(self, data):
        try:
            graph, op = _switch_graph(
                data, self.query_graph, self.mutation_graph,
            )
            result = self.execute(graph, op, {})
            return {'data': result}
        except GraphQLError as e:
            return {'errors': [{'message': e} for e in e.errors]}
