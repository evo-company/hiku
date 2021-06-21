from abc import abstractmethod
from contextlib import contextmanager
from federation.engine import get_keys
from typing import (
    List,
    Dict,
    Any,
)

from federation.introspection import (
    FederatedGraphQLIntrospection,
    AsyncFederatedGraphQLIntrospection,
)

from federation.sdl import print_sdl
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
from federation.graph import FederatedGraph
from hiku.query import Node
from hiku.result import Proxy, Reference


def denormalize_entity(entity, result):
    res = {}
    index = result.__idx__

    def _denormalize(val):
        if isinstance(val, list):
            return [_denormalize(item) for item in val]
        elif isinstance(val, Reference):
            data = index[val.node]
            return data[val.ident]
        else:
            return val

    for key, val in entity.items():
        res[key] = _denormalize(val)

    return res


def denormalize_entities(
    graph: FederatedGraph,
    query: Node,
    result: Proxy
) -> List[Dict[str, Any]]:
    entities_link = query.fields_map['_entities']
    representations = entities_link.options['representations']

    entities = []
    for rep in representations:
        typename = rep['__typename']

        data = result.__idx__[typename]
        keys = get_keys(graph, typename)

        # TODO implement multiple keys like ['id', 'sku']
        entity = {}
        for key in keys:
            ident = rep[key]
            entity = data[ident]
            if isinstance(entity, dict):
                entity = denormalize_entity(entity, result)

        entities.append(entity)

    return entities


class BaseFederatedGraphEndpoint(BaseGraphQLEndpoint):
    @abstractmethod
    def execute(self, graph, op, ctx):
        pass

    @abstractmethod
    def dispatch(self, data):
        pass

    @contextmanager
    def context(self, op):
        yield {}

    @staticmethod
    def process_service_query(graph):
        return {'_service': {'sdl': print_sdl(graph)}}

    @staticmethod
    def postprocess_result(result, graph, op):
        type_name = _type_names[op.type]

        if '_entities' in op.query.fields_map:
            data = {'_entities': denormalize_entities(graph, op.query, result)}
        else:
            data = DenormalizeGraphQL(graph, result, type_name).process(op.query)
        return data


class FederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    """Can execute either regular or federated queries.
    Handles following fields of federated query:
        - _service
        - _entities
    """
    introspection_cls = FederatedGraphQLIntrospection

    def execute(self, graph: FederatedGraph, op, ctx):
        if '_service' in op.query.fields_map:
            return self.process_service_query(graph)

        stripped_query = _process_query(graph, op.query)
        result = self.engine.execute(graph, stripped_query, ctx)
        return self.postprocess_result(result, graph, op)

    def dispatch(self, data):
        try:
            graph, op = _switch_graph(
                data, self.query_graph, self.mutation_graph,
            )
            with self.context(op) as ctx:
                result = self.execute(graph, op, ctx)
            return {'data': result}
        except GraphQLError as e:
            return {'errors': [{'message': e} for e in e.errors]}


class AsyncFederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    introspection_cls = AsyncFederatedGraphQLIntrospection

    async def execute(self, graph: FederatedGraph, op, ctx):
        if '_service' in op.query.fields_map:
            return self.process_service_query(graph)

        stripped_query = _process_query(graph, op.query)
        result = await self.engine.execute(graph, stripped_query, ctx)
        return self.postprocess_result(result, graph, op)

    async def dispatch(self, data):
        try:
            graph, op = _switch_graph(
                data, self.query_graph, self.mutation_graph,
            )
            with self.context(op) as ctx:
                result = await self.execute(graph, op, ctx)
            return {'data': result}
        except GraphQLError as e:
            return {'errors': [{'message': e} for e in e.errors]}
