from collections import defaultdict
from typing import (
    List,
    Protocol,
    TypeVar,
    NamedTuple,
)

from federation.sdl import print_sdl
from hiku.engine import (
    InitOptions,
    Query,
    Context,
)
from hiku.executors.queue import Queue
from hiku.graph import Graph
from hiku.result import Proxy


class KeyNotFound(Exception):
    def __init__(self, key, rep):
        super().__init__(f'No key "{key}" in representation "{rep}"')


def get_keys(graph, typename) -> List[int]:
    node = graph.nodes_map[typename]
    return [
        d.args_map['fields'].value for d in
        filter(lambda d: d.name == 'key', node.directives)
    ]


RT = TypeVar('RT')


class Result(Protocol):
    data: RT


class QueryResult(NamedTuple):
    data: Proxy


class ServiceResult(NamedTuple):
    data: str


class EntitiesResult(NamedTuple):
    data: Proxy


class Engine:
    def __init__(self, executor):
        self.executor = executor

    def execute_service(self, graph):
        return ServiceResult(print_sdl(graph))

    def execute_entities(self, graph, query, ctx):
        entities_link = query.fields_map['_entities']
        query = entities_link.node

        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        representations = entities_link.options['representations']

        type_ids_map = defaultdict(list)

        for rep in representations:
            typename = rep['__typename']
            keys = get_keys(graph, typename)
            # TODO refactor [0], apollo has __resolveReference to pass ident as is
            key = keys[0]
            if key not in rep:
                raise KeyNotFound(key, rep)
            ident = rep[key]

            type_ids_map[typename].append(ident)

        for typename in type_ids_map:
            ids = type_ids_map[typename]
            node = graph.nodes_map[typename]
            query_workflow.process_node(node, query, ids)

        return EntitiesResult(self.executor.process(queue, query_workflow))

    def execute_query(self, graph, query, ctx):
        query = InitOptions(graph).visit(query)
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        query_workflow.start()
        return QueryResult(self.executor.process(queue, query_workflow))

    def execute(self, graph: Graph, query, ctx=None) -> Result:
        if ctx is None:
            ctx = {}

        if '_service' in query.fields_map:
            return self.execute_service(graph)
        elif '_entities' in query.fields_map:
            return self.execute_entities(graph, query, ctx)

        return self.execute_query(graph, query, ctx)
