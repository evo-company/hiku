from collections import defaultdict
from typing import (
    Optional,
    Dict,
    Awaitable,
    TYPE_CHECKING, Union,
)

from hiku.cache import CacheInfo, CacheSettings
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.executors.base import SyncAsyncExecutor
from hiku.federation.sdl import print_sdl
from hiku.federation.utils import get_representation_ident
from hiku.engine import (
    BaseEngine, InitOptions,
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
from hiku.query import (
    Node,
    Field,
)


if TYPE_CHECKING:
    from hiku.readers.graphql import Operation


async def async_result(val):
    return val


class Engine(BaseEngine):
    def __init__(
        self,
        executor: SyncAsyncExecutor,
        cache: Optional[CacheSettings] = None,
        enable_v2: bool = False,
    ) -> None:
        super().__init__(executor, cache)
        self.enable_v2 = enable_v2

    def execute_service(self, graph: Graph) -> Union[Proxy, Awaitable[Proxy]]:
        idx = Index()
        idx[ROOT.node] = Index()
        idx[ROOT.node][ROOT.ident] = {"sdl": print_sdl(graph, self.enable_v2)}
        result = Proxy(idx, ROOT, Node(fields=[Field("sdl")]))
        if isinstance(self.executor, AsyncIOExecutor):
            return async_result(result)
        return result

    def execute_entities(
        self, graph: Graph, query: Node, ctx: Dict
    ) -> Union[Proxy, Awaitable[Proxy]]:
        path = ("_entities",)
        entities_link = query.fields_map["_entities"]
        query = entities_link.node
        representations = entities_link.options["representations"]

        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        type_ids_map = defaultdict(list)

        for rep in representations:
            typename = rep["__typename"]
            ident = get_representation_ident(rep, graph)
            type_ids_map[typename].append(ident)

        for typename in type_ids_map:
            ids = type_ids_map[typename]
            node = graph.nodes_map[typename]
            # TODO(mkind): here we must execute resolve_reference function and only then
            #  run process_node !
            query_workflow.process_node(path, node, query, ids)

        return self.executor.process(queue, query_workflow)

    def execute_query(
        self, graph: Graph, query: Node, ctx: Dict
    ) -> Union[Proxy, Awaitable[Proxy]]:
        query = InitOptions(graph).visit(query)
        queue = Queue(self.executor)
        task_set = queue.fork(None)

        cache = (
            CacheInfo(
                self.cache_settings,
                op.name if op else None,
            )
            if self.cache_settings
            else None
        )

        query_workflow = Query(queue, task_set, graph, query, Context(ctx), cache)

        query_workflow.start()
        return self.executor.process(queue, query_workflow)

    def execute(
        self,
        graph: Graph,
        query: Node,
        ctx: Optional[Dict] = None,
        op: Optional["Operation"] = None,
    ) -> Union[Proxy, Awaitable[Proxy]]:
        if ctx is None:
            ctx = {}

        if "_service" in query.fields_map:
            return self.execute_service(graph)
        elif "_entities" in query.fields_map:
            return self.execute_entities(graph, query, ctx)

        return self.execute_query(graph, query, ctx)
