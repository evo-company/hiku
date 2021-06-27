from collections import defaultdict

from federation.sdl import print_sdl
from federation.utils import get_keys
from hiku.engine import (
    InitOptions,
    Query,
    Context,
)
from hiku.executors.queue import Queue
from hiku.graph import Graph
from hiku.result import (
    Proxy,
    Index,
)


class Engine:
    def __init__(self, executor):
        self.executor = executor

    def execute_service(self, graph):
        idx = Index()
        idx['sdl'] = print_sdl(graph)
        return Proxy(idx, None, None)

    def _execute_entities(self, graph, query, ctx):
        entities_link = query.fields_map['_entities']
        query = entities_link.node
        representations = entities_link.options['representations']

        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        type_ids_map = defaultdict(list)

        for rep in representations:
            typename = rep['__typename']
            for key in get_keys(graph, typename):
                if key not in rep:
                    continue
                # TODO validate - what if none keys in reps ?
                #  Or this should be handled by federation ?
                ident = rep[key]

                type_ids_map[typename].append(ident)

        for typename in type_ids_map:
            ids = type_ids_map[typename]
            node = graph.nodes_map[typename]
            query_workflow.process_node(node, query, ids)

        return self.executor.process(queue, query_workflow)

    # TODO For AnyIOExecutor this can fail
    def execute_entities(self, graph, query, ctx):
        return self._execute_entities(graph, query, ctx)

    async def execute_entities_async(self, graph, query, ctx):
        return await self._execute_entities(graph, query, ctx)

    def _execute_query(self, graph, query, ctx):
        query = InitOptions(graph).visit(query)
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        query_workflow.start()
        return self.executor.process(queue, query_workflow)

    # TODO For AnyIOExecutor this can fail
    def execute_query(self, graph, query, ctx):
        return self._execute_query(graph, query, ctx)

    async def execute_query_async(self, graph, query, ctx):
        return await self._execute_query(graph, query, ctx)

    def execute(self, graph: Graph, query, ctx=None) -> Proxy:
        if ctx is None:
            ctx = {}

        if '_service' in query.fields_map:
            return self.execute_service(graph)
        elif '_entities' in query.fields_map:
            return self.execute_entities(graph, query, ctx)

        return self.execute_query(graph, query, ctx)

    async def execute_async(self, graph: Graph, query, ctx=None) -> Proxy:
        if ctx is None:
            ctx = {}

        if '_service' in query.fields_map:
            return self.execute_service(graph)
        elif '_entities' in query.fields_map:
            return await self.execute_entities_async(graph, query, ctx)

        return await self.execute_query_async(graph, query, ctx)
