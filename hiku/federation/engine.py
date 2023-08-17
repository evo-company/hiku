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
from hiku.executors.base import SyncAsyncExecutor
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
from hiku.result import Proxy
from hiku.query import Node


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

    def execute(
        self,
        graph: Graph,
        query: Node,
        ctx: Optional[Dict] = None,
        op: Optional["Operation"] = None,
    ) -> Union[Proxy, Awaitable[Proxy]]:
        if not ctx:
            ctx = {}

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
