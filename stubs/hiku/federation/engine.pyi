from ..executors.base import SyncAsyncExecutor as SyncAsyncExecutor
from ..query import Field as Field, Node as Node
from .sdl import print_sdl as print_sdl
from .utils import get_keys as get_keys
from _typeshed import Incomplete
from hiku.engine import Context as Context, InitOptions as InitOptions, Query as Query
from hiku.executors.queue import Queue as Queue
from hiku.graph import Graph as Graph
from hiku.result import Index as Index, Proxy as Proxy, ROOT as ROOT
from typing import Awaitable, Dict, Optional, Union

class Engine:
    executor: Incomplete
    def __init__(self, executor: SyncAsyncExecutor) -> None: ...
    def execute_service(self, graph: Graph) -> Proxy: ...
    def execute_entities(self, graph: Graph, query: Node, ctx: Dict) -> Union[Proxy, Awaitable[Proxy]]: ...
    def execute_query(self, graph: Graph, query: Node, ctx: Dict) -> Union[Proxy, Awaitable[Proxy]]: ...
    def execute(self, graph: Graph, query: Node, ctx: Optional[Dict] = ...) -> Union[Proxy, Awaitable[Proxy]]: ...
