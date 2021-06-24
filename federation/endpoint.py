from abc import abstractmethod
from asyncio import gather
from contextlib import contextmanager
from federation.engine import (
    get_keys,
    Result,
    ServiceResult,
    EntitiesResult,
)
from typing import (
    List,
    Dict,
    Any,
)

from federation.introspection import (
    FederatedGraphQLIntrospection,
    AsyncFederatedGraphQLIntrospection,
    is_introspection_query,
    extend_with_federation,
)
from federation.validate import validate

from hiku.denormalize.graphql import (
    DenormalizeGraphQL,
)
from hiku.endpoint.graphql import (
    BaseGraphQLEndpoint,
    _type_names,
    _switch_graph,
    GraphQLError,
    _StripQuery,
)
from hiku.graph import Graph
from hiku.query import Node
from hiku.result import Proxy, Reference


def _process_query(graph, query):
    stripped_query = _StripQuery().visit(query)
    errors = validate(graph, stripped_query)
    if errors:
        raise GraphQLError(errors=errors)
    else:
        return stripped_query


def denormalize_entity(entity, result):
    def _denormalize(value):
        if isinstance(value, list):
            return [_denormalize(item) for item in value]
        if isinstance(value, dict):
            return {key: _denormalize(val) for key, val in value.items() if not key.startswith('_')}
        elif isinstance(value, Reference):
            return _denormalize(result.__idx__[value.node][value.ident])
        else:
            return value

    return _denormalize(entity)


def denormalize_entities(
    graph: Graph,
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
    def postprocess_result(result: Result, graph, op):
        if isinstance(result, ServiceResult):
            return {'_service': {'sdl': result.data}}
        elif isinstance(result, EntitiesResult):
            return {
                '_entities': denormalize_entities(graph, op.query, result.data)
            }

        type_name = _type_names[op.type]

        data = DenormalizeGraphQL(graph, result.data, type_name).process(op.query)
        if is_introspection_query(op.query):
            extend_with_federation(graph, data)
        return data


class FederatedGraphQLEndpoint(BaseFederatedGraphEndpoint):
    """Can execute either regular or federated queries.
    Handles following fields of federated query:
        - _service
        - _entities
    """
    introspection_cls = FederatedGraphQLIntrospection

    def execute(self, graph: Graph, op, ctx):
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

    async def execute(self, graph: Graph, op, ctx):
        stripped_query = _process_query(graph, op.query)
        result = await self.engine.execute_async(graph, stripped_query, ctx)
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


class AsyncBatchFederatedGraphQLEndpoint(AsyncFederatedGraphQLEndpoint):
    async def dispatch(self, data):
        if isinstance(data, list):
            return await gather(*(
                super().dispatch(item)
                for item in data
            ))
        else:
            return await super().dispatch(data)
