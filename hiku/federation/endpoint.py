from abc import ABC
from asyncio import gather
from contextlib import contextmanager
from typing import (
    List,
    Dict,
    Any,
    Optional,
    Tuple,
    overload,
    Iterator,
    Union,
)

from .utils import get_keys
from .introspection import (
    FederatedGraphQLIntrospection,
    AsyncFederatedGraphQLIntrospection,
    is_introspection_query,
    extend_with_federation,
)
from .validate import validate

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.federation.denormalize import DenormalizeEntityGraphQL
from hiku.endpoint.graphql import (
    BaseSyncGraphQLEndpoint,
    BaseAsyncGraphQLEndpoint,
    _type_names,
    _switch_graph,
    GraphQLError,
    _StripQuery,
    BaseGraphQLEndpoint,
)
from hiku.graph import Graph
from hiku.query import Node
from hiku.result import Proxy, Reference
from hiku.readers.graphql import Operation


def _process_query(graph: Graph, query: Node) -> Node:
    stripped_query = _StripQuery().visit(query)
    errors = validate(graph, stripped_query)
    if errors:
        raise GraphQLError(errors=errors)
    else:
        return stripped_query


def denormalize_entities(
    graph: Graph,
    query: Node,
    result: Proxy,
) -> List[Dict[str, Any]]:

    entities_link = query.fields_map['_entities']
    node = entities_link.node
    representations = entities_link.options['representations']

    entities = []
    for r in representations:
        typename = r['__typename']
        for key in get_keys(graph, typename):
            if key not in r:
                continue
            ident = r[key]
            result.__ref__ = Reference(typename, ident)
            data = DenormalizeEntityGraphQL(
                graph, result, typename
            ).process(node)
            entities.append(data)

    return entities


class BaseFederatedGraphEndpoint(BaseGraphQLEndpoint, ABC):
    @contextmanager
    def context(self, op: Operation) -> Iterator[Dict]:
        yield {}

    @staticmethod
    def postprocess_result(result: Proxy, graph: Graph, op: Operation) -> Dict:
        if '_service' in op.query.fields_map:
            return {'_service': {'sdl': result['sdl']}}
        elif '_entities' in op.query.fields_map:
            return {
                '_entities': denormalize_entities(
                    graph, op.query, result
                )
            }

        type_name = _type_names[op.type]

        data = DenormalizeGraphQL(graph, result, type_name).process(op.query)
        if is_introspection_query(op.query):
            extend_with_federation(graph, data)
        return data


class FederatedGraphQLEndpoint(
    BaseSyncGraphQLEndpoint, BaseFederatedGraphEndpoint
):
    """Can execute either regular or federated queries.
    Handles following fields of federated query:
        - _service
        - _entities
    """
    introspection_cls = FederatedGraphQLIntrospection

    def execute(
        self, graph: Graph, op: Operation, ctx: Optional[Dict]
    ) -> Dict:
        stripped_query = _process_query(graph, op.query)
        result = self.engine.execute(graph, stripped_query, ctx)
        return self.postprocess_result(result, graph, op)

    def dispatch(self, data: Dict) -> Dict:
        try:
            graph, op = _switch_graph(
                data, self.query_graph, self.mutation_graph,
            )
            with self.context(op) as ctx:
                result = self.execute(graph, op, ctx)
            return {'data': result}
        except GraphQLError as e:
            return {'errors': [{'message': e} for e in e.errors]}


class AsyncFederatedGraphQLEndpoint(
    BaseAsyncGraphQLEndpoint, BaseFederatedGraphEndpoint
):
    introspection_cls = AsyncFederatedGraphQLIntrospection

    async def execute(
        self, graph: Graph, op: Operation, ctx: Optional[Dict]
    ) -> Dict:
        stripped_query = _process_query(graph, op.query)
        result = await self.engine.execute_async(graph, stripped_query, ctx)
        return self.postprocess_result(result, graph, op)

    async def dispatch(self, data: Dict) -> Dict:
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
    @overload
    async def dispatch(self, data: List[Dict]) -> Tuple[Dict, ...]:
        ...

    @overload
    async def dispatch(self, data: Dict) -> Dict:
        ...

    async def dispatch(
        self, data: Union[Dict, List[Dict]]
    ) -> Union[Dict, Tuple[Dict, ...]]:
        if isinstance(data, list):
            return await gather(*(
                super().dispatch(item)
                for item in data
            ))

        return await super().dispatch(data)
