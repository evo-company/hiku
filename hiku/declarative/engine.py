'''Exploring ways to build generic workflow for new resolvers'''

from typing import (
    Any,
    Generic,
    TypeVar,
    Optional,
)
from collections import defaultdict
from collections.abc import Mapping

from ..query import (
    Node as QueryNode,
)
from .graph import (
    Graph,
    Node,
)
from ..result import (
    Proxy,
    Index,
    ROOT,
    Reference,
)
from ..executors.queue import (
    Workflow,
    Queue,
    TaskSet,
)


_T = TypeVar('_T')


def serialize_value(typ: type, value: _T) -> _T | Any:
    if isinstance(typ, Node):
        return Reference(typ, value)
    if isinstance(typ, list):
        return [serialize_value(typ.subtype, v) for v in value]
    if isinstance(typ, Optional):
        return (
            serialize_value(typ.subtype, value)
            if value is not None else None
        )
    return value


def store_field(
    index: Index,
    typ: Node,
    keys: list[Any],
    field: Any,
    res: Any,
):
    for key, value in zip(keys, res):
        index[typ.name][key][field.index_key] = serialize_value(
            field.typ,
            value,
        )


_TContext = TypeVar('_TContext', bound=Mapping)


class QueryDeclarative(Workflow, Generic[_TContext]):

    def __init__(
        self,
        queue: Queue,
        task_set: TaskSet,
        graph: Graph,
        query: QueryNode,
        ctx: _TContext,
    ):
        self._queue = queue
        self._task_set = task_set
        self._graph = graph
        self._query = query
        self._ctx = ctx
        self._index = Index()

    def start(self):
        self.process_type(self._graph.root, self._query, [None])

    def result(self) -> Proxy:
        self._index.finish()
        return Proxy(self._index, ROOT, self._query)

    def process_type(self, typ, query, keys):
        if not isinstance(typ, Node):
            return

        fields = query.get_fields()

        preload_to_fields = defaultdict(list)
        for field in fields:
            preload_to_fields[field.preload].append(field)

        for func, fields in preload_to_fields.items():
            preload_future = self._task_set.submit(func, keys, self._ctx)

            def resolve_dependants():
                keys_preloaded = preload_future.result()
                for field in fields:
                    dep = self._task_set.submit(
                        field.resolve,
                        keys_preloaded,
                        field.opts,
                        self._ctx,
                    )

                    def store_cb():
                        res = dep.result()
                        store_field(self._index, typ, keys, field, res)
                        self.process_type(field.type, query.field, res)

                    self._queue.add_callback(dep, store_cb)

            self._queue.add_callback(preload_future, resolve_dependants)
