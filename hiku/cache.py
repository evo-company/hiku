import abc
import contextlib
import hashlib

from collections import (
    defaultdict,
    deque,
)
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Union,
    Deque,
    Iterator,
    Optional,
    Callable,
    Protocol,
)

from prometheus_client import Counter

from hiku.result import Index
from hiku.graph import (
    Many,
    Graph,
    Node,
    Field,
)
from hiku.query import (
    QueryVisitor,
    Field as QueryField,
    Link as QueryLink,
    Node as QueryNode,
)

if TYPE_CHECKING:
    from hiku.engine import Context


RESULT_CACHE_HITS = Counter(
    name="hiku_result_cache_hits",
    documentation="Resolver result cache hits",
    labelnames=["graph", "query_name", "node", "field"],
)
RESULT_CACHE_MISSES = Counter(
    name="hiku_result_cache_misses",
    documentation="Resolver result cache misses",
    labelnames=["graph", "query_name", "node", "field"],
)

CACHE_VERSION = "2"


class Hasher(Protocol):
    def update(self, data: bytes) -> None: ...


CacheKeyFn = Callable[["Context", Hasher], None]


class BaseCache(abc.ABC):
    @abc.abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Result must contain only keys which were cached"""
        raise NotImplementedError()

    @abc.abstractmethod
    def set_many(self, items: Dict[str, Any], ttl: int) -> None:
        raise NotImplementedError()


@dataclass
class CacheMetrics:
    name: str
    hits_counter: Counter = RESULT_CACHE_HITS
    misses_counter: Counter = RESULT_CACHE_MISSES


@dataclass
class CacheSettings:
    cache: BaseCache
    cache_key: Optional[CacheKeyFn] = None
    metrics: Optional[CacheMetrics] = None


class CacheInfo:
    __slots__ = ("cache", "cache_key", "metrics", "query_name")

    def __init__(
        self, cache_settings: CacheSettings, query_name: Optional[str] = None
    ):
        self.cache = cache_settings.cache
        self.cache_key = cache_settings.cache_key
        self.metrics = cache_settings.metrics
        self.query_name = query_name or "unknown"

    def _track(self, node: str, field: str, hits: int, misses: int) -> None:
        if not self.metrics:
            return

        self.metrics.hits_counter.labels(
            self.metrics.name, self.query_name, node, field
        ).inc(hits)
        self.metrics.misses_counter.labels(
            self.metrics.name, self.query_name, node, field
        ).inc(misses)

    def query_hash(
        self, ctx: "Context", query_link: QueryLink, req: Any
    ) -> str:
        hasher = hashlib.sha1()
        get_query_hash(hasher, query_link, req)
        if self.cache_key:
            self.cache_key(ctx, hasher)
        return hasher.hexdigest()

    def get_many(
        self, keys: List[str], node: str, field: str
    ) -> Dict[str, Any]:
        data = self.cache.get_many(keys)
        hits = sum(1 for key in keys if key in data)
        misses = len(keys) - hits
        self._track(node, field, hits, misses)
        return data

    def set_many(self, items: Dict[str, Any], ttl: int) -> None:
        self.cache.set_many(items, ttl)


class HashVisitor(QueryVisitor):
    def __init__(self, hasher) -> None:  # type: ignore
        self._hasher = hasher

    def visit_field(self, obj: QueryField) -> None:
        self._hasher.update(obj.index_key.encode())

    def visit_node(self, obj: QueryNode) -> None:
        for field in obj.fields:
            self.visit(field)

        for fr in obj.fragments:
            self.visit(fr)

    def visit_link(self, obj: QueryLink) -> None:
        self._hasher.update(obj.index_key.encode())
        super().visit_link(obj)


class CacheVisitor(QueryVisitor):
    """Visit cached query link to extract all data from index
    that needs to be cached
    """

    def __init__(
        self, cache: CacheInfo, index: Index, graph: Graph, node: Node
    ) -> None:
        self._cache = cache
        self._index = index
        self._graph = graph
        self._node = deque([node])
        self._req: Deque[Any] = deque()
        self._data: Deque[Dict] = deque()
        self._to_cache: Deque[Dict] = deque()
        self._node_idx: Deque[Dict] = deque()

    def visit_field(self, field: QueryField) -> None:
        if field.name == "__typename":
            return

        self._data[-1][field.index_key] = self._node_idx[-1][field.index_key]
        super().visit_field(field)

    def visit_node(self, node: QueryNode) -> None:
        for field in node.fields:
            self.visit(field)

        for fr in node.fragments:
            self.visit(fr)

    def visit_link(self, link: QueryLink) -> None:
        refs = self._node_idx[-1][link.index_key]

        self._data[-1][link.index_key] = refs

        graph_obj = self._node[-1].fields_map[link.name]
        if isinstance(graph_obj, Field):
            # Link as complex field
            return

        node = self._graph.nodes_map[graph_obj.node]
        self._node.append(node)

        @contextlib.contextmanager
        def _visit_ctx(req: Any) -> Iterator:
            self._node_idx.append(self._index[node.name][req])
            self._data.append({})

            yield

            data = self._data.pop()
            self._to_cache[-1][node.name][req] = data
            self._node_idx.pop()

        if graph_obj.type_enum is Many:
            for r in refs:
                with _visit_ctx(r.ident):
                    super().visit_link(link)
        else:
            if refs is None:
                self._node.pop()
                return

            with _visit_ctx(refs.ident):
                super().visit_link(link)

        self._node.pop()

    def process(
        self, link: QueryLink, ids: List, reqs: List, ctx: "Context"
    ) -> Dict:
        to_cache = {}
        for i, req in zip(ids, reqs):
            node = self._node[-1]
            self._node_idx.append(self._index[node.name][i])
            self._data.append({})
            self._to_cache.append(defaultdict(dict))

            self.visit(link)

            self._to_cache[-1][node.name] = self._data.pop()
            key = self._cache.query_hash(ctx, link, req)
            to_cache[key] = dict(self._to_cache.pop())
            self._node_idx.pop()

        return to_cache


def get_query_hash(
    hasher: Hasher, query_link: Union[QueryLink, QueryField], req: Any
) -> None:
    hash_visitor = HashVisitor(hasher)
    hash_visitor.visit(query_link)

    if isinstance(req, list):
        for r in req:
            hasher.update(str(hash(r)).encode("utf-8"))
    else:
        hasher.update(str(hash(req)).encode("utf-8"))
    hasher.update(CACHE_VERSION.encode("utf-8"))
