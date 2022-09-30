import abc
import contextlib
import hashlib

from collections import (
    defaultdict,
    deque,
)
from typing import (
    Any,
    Dict,
    List,
    Union,
    Deque,
    Iterator,
)

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
)


CACHE_VERSION = '1'


class BaseCache(abc.ABC):
    @abc.abstractmethod
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Result must contain only keys which were cached"""
        raise NotImplementedError()

    @abc.abstractmethod
    def set_many(self, items: Dict[str, Any], ttl: int) -> None:
        raise NotImplementedError()


class HashVisitor(QueryVisitor):
    def __init__(self, hasher) -> None:  # type: ignore
        self._hasher = hasher

    def visit_field(self, obj: QueryField) -> None:
        self._hasher.update(obj.index_key.encode())

    def visit_link(self, obj: QueryLink) -> None:
        self._hasher.update(obj.index_key.encode())
        super().visit_link(obj)


class CacheVisitor(QueryVisitor):
    """Visit cached query link to extract all data from index
    that needs to be cached
    """
    def __init__(self, index: Index, graph: Graph, node: Node) -> None:
        self._index = index
        self._graph = graph
        self._node = deque([node])
        self._req: Deque[Any] = deque()
        self._data: Deque[Dict] = deque()
        self._to_cache: Deque[Dict] = deque()
        self._node_idx: Deque[Dict] = deque()

    def visit_field(self, field: QueryField) -> None:
        self._data[-1][field.index_key] = self._node_idx[-1][field.index_key]
        super().visit_field(field)

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

    def process(self, link: QueryLink, ids: List, reqs: List) -> Dict:
        to_cache = {}
        for i, req in zip(ids, reqs):
            node = self._node[-1]
            self._node_idx.append(self._index[node.name][i])
            self._data.append({})
            self._to_cache.append(defaultdict(dict))

            self.visit(link)

            self._to_cache[-1][node.name] = self._data.pop()
            to_cache[get_query_hash(link, req)] = dict(self._to_cache.pop())
            self._node_idx.pop()

        return to_cache


def get_query_hash(
    query_link: Union[QueryLink, QueryField],
    req: Any
) -> str:
    hasher = hashlib.sha1()
    hash_visitor = HashVisitor(hasher)
    hash_visitor.visit(query_link)

    if isinstance(req, list):
        for r in req:
            hasher.update(str(hash(r)).encode('utf-8'))
    else:
        hasher.update(str(hash(req)).encode('utf-8'))
    hasher.update(CACHE_VERSION.encode('utf-8'))
    return hasher.hexdigest()
