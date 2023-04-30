from collections import defaultdict
from typing import (
    Optional,
    Dict,
    Awaitable,
    Union,
)

from hiku.federation.v2.sdl import print_sdl
from hiku.federation.v2.utils import get_keys
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
    ROOT,
)
from hiku.executors.base import SyncAsyncExecutor
from hiku.query import (
    Node,
    Field,
)


class Engine:
    def __init__(self, executor: SyncAsyncExecutor):
        self.executor = executor

    def execute_service(self, graph: Graph) -> Proxy:
        idx = Index()
        idx[ROOT.node] = Index()
        idx[ROOT.node][ROOT.ident] = {'sdl': print_sdl(graph)}
        return Proxy(idx, ROOT, Node(fields=[Field('sdl')]))

    def execute_entities(
        self,
        graph: Graph,
        query: Node,
        ctx: Dict
    ) -> Union[Proxy, Awaitable[Proxy]]:
        path = ('_entities',)
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
                ident = rep[key]

                type_ids_map[typename].append(ident)

        for typename in type_ids_map:
            ids = type_ids_map[typename]
            node = graph.nodes_map[typename]
            query_workflow.process_node(path, node, query, ids)

        return self.executor.process(queue, query_workflow)

    def execute_query(
        self,
        graph: Graph,
        query: Node,
        ctx: Dict
    ) -> Union[Proxy, Awaitable[Proxy]]:
        query = InitOptions(graph).visit(query)
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        query_workflow.start()
        return self.executor.process(queue, query_workflow)

    def execute(
        self,
        graph: Graph,
        query: Node,
        ctx: Optional[Dict] = None
    ) -> Union[Proxy, Awaitable[Proxy]]:
        if ctx is None:
            ctx = {}

        if '_service' in query.fields_map:
            return self.execute_service(graph)
        elif '_entities' in query.fields_map:
            return self.execute_entities(graph, query, ctx)

        return self.execute_query(graph, query, ctx)
