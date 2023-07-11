from collections import defaultdict
from typing import (
    Optional,
    Dict,
    Awaitable,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

from hiku.types import Sequence, TypeRef, Optional as HikuOptional

from hiku.cache import CacheInfo, CacheSettings
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.executors.base import SyncAsyncExecutor
from hiku.federation.sdl import print_sdl
from hiku.federation.utils import representation_to_ident
from hiku.engine import (
    BaseEngine,
    InitOptions,
    Query,
    Context,
)
from hiku.executors.queue import Queue
from hiku.federation.version import DEFAULT_FEDERATION_VERSION
from hiku.graph import (
    Graph,
    GraphTransformer,
    Link,
    Many,
    Maybe,
    One,
)
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


V = TypeVar("V")


async def async_result(val: V) -> V:
    return val


def union_link_to_type(obj: Link, typ: str) -> Link:
    link = GraphTransformer().visit_link(obj)

    link.node = typ
    if link.type_enum is One:
        link.type = TypeRef[typ]
    elif link.type_enum is Maybe:
        link.type = HikuOptional[TypeRef[typ]]
    elif link.type_enum is Many:
        link.type = Sequence[TypeRef[typ]]
    else:
        raise TypeError(repr(link.type_enum))
    return link


class Engine(BaseEngine):
    def __init__(
        self,
        executor: SyncAsyncExecutor,
        cache: Optional[CacheSettings] = None,
        federation_version: int = DEFAULT_FEDERATION_VERSION,
    ) -> None:
        super().__init__(executor, cache)
        if federation_version not in (1, 2):
            raise ValueError("federation_version must be 1 or 2")
        self.federation_version = federation_version

    def execute_service(
        self, graph: Graph, mutation_graph: Optional[Graph]
    ) -> Union[Proxy, Awaitable[Proxy]]:
        idx = Index()
        idx[ROOT.node] = Index()
        idx[ROOT.node][ROOT.ident] = {
            "sdl": print_sdl(
                graph,
                mutation_graph,
                federation_version=self.federation_version,
            )
        }
        result = Proxy(idx, ROOT, Node(fields=[Field("sdl")]))
        if isinstance(self.executor, AsyncIOExecutor):
            return async_result(result)
        return result

    def execute_entities(
        self, graph: Graph, query: Node, ctx: Dict
    ) -> Union[Proxy, Awaitable[Proxy]]:
        path = ("_entities",)
        representations = query.fields_map["_entities"].options[
            "representations"
        ]

        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))

        type_representations_map = defaultdict(list)

        for rep in representations:
            typename = rep["__typename"]
            ident = representation_to_ident(rep)
            type_representations_map[typename].append(ident)

        for typename, ids in type_representations_map.items():
            query_workflow.process_node(path, graph.root, query, ids)

        return self.executor.process(queue, query_workflow)

    def execute_query(
        self, graph: Graph, query: Node, ctx: Dict, op: Optional["Operation"]
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

        query_workflow = Query(
            queue, task_set, graph, query, Context(ctx), cache
        )

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

        if "_entities" in query.fields_map:
            return self.execute_entities(graph, query, ctx)

        return self.execute_query(graph, query, ctx, op)
