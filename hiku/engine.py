import contextlib
import inspect
import warnings
import dataclasses

from typing import (
    Any,
    Generic,
    TypeVar,
    Callable,
    cast,
    Iterator,
    Tuple,
    Union,
    Dict,
    List,
    Set,
    NoReturn,
    Optional,
    DefaultDict,
    overload,
)
from functools import partial
from itertools import chain, repeat
from collections import defaultdict
from collections.abc import Sequence, Mapping, Hashable

from .cache import (
    CacheVisitor,
    CacheInfo,
    CacheSettings,
)
from .compat import Concatenate, ParamSpec
from .context import ExecutionContext
from .executors.base import (
    BaseAsyncExecutor,
    BaseSyncExecutor,
    SyncAsyncExecutor,
)
from .query import (
    Fragment,
    Node as QueryNode,
    Field as QueryField,
    Link as QueryLink,
    QueryTransformer,
    QueryVisitor,
)
from .graph import (
    FieldType,
    Link,
    LinkType,
    Maybe,
    MaybeMany,
    One,
    Many,
    Nothing,
    Field,
    Graph,
    Node,
)
from .result import (
    Proxy,
    Index,
    ROOT,
    Reference,
)
from .executors.queue import (
    Workflow,
    Queue,
    TaskSet,
    SubmitRes,
)
from .utils import ImmutableDict
from .utils.serialize import serialize


NodePath = Tuple[Optional[str], ...]


def _yield_options(
    graph: Graph,
    graph_obj: Union[Link, Field],
    query_obj: Union[QueryField, QueryLink],
) -> Iterator[Tuple[str, Any]]:
    options = query_obj.options or {}
    for option in graph_obj.options:
        value = options.get(option.name, option.default)
        if value is Nothing:
            raise TypeError(
                'Required option "{}" for {!r} was not provided'.format(
                    option.name, graph_obj
                )
            )
        elif option.type_info and option.type_info.type_enum is FieldType.ENUM:
            enum = graph.enums_map[option.type_info.type_name]
            yield option.name, serialize(option.type, value, enum.parse)
        elif (
            option.type_info
            and option.type_info.type_enum is FieldType.CUSTOM_SCALAR
        ):
            scalar = graph.scalars_map[option.type_info.type_name]
            yield option.name, serialize(option.type, value, scalar.parse)
        else:
            yield option.name, value


def _get_options(
    graph: Graph,
    graph_obj: Union[Link, Field],
    query_obj: Union[QueryField, QueryLink],
) -> Dict:
    return dict(_yield_options(graph, graph_obj, query_obj))


class InitOptions(QueryTransformer):
    def __init__(self, graph: Graph) -> None:
        self._graph = graph
        self._path = [graph.root]

    @contextlib.contextmanager
    def enter_path(self, type_: Any) -> Iterator[None]:
        try:
            if type_ is not None:
                self._path.append(type_)
            yield
        finally:
            if type_ is not None:
                self._path.pop()

    def visit_node(self, obj: QueryNode) -> QueryNode:
        fields = []
        fragments = []

        for f in obj.fields:
            if f.name == "__typename":
                fields.append(f)
            else:
                fields.append(self.visit(f))

        for fr in obj.fragments:
            with self.enter_path(self._graph.nodes_map[fr.type_name]):
                fragments.append(self.visit(fr))

        return obj.copy(fields=fields, fragments=fragments)

    def visit_field(self, obj: QueryField) -> QueryField:
        graph_obj = self._path[-1].fields_map[obj.name]
        if graph_obj.options:
            return obj.copy(options=_get_options(self._graph, graph_obj, obj))
        else:
            return obj

    def visit_link(self, obj: QueryLink) -> QueryLink:
        graph_obj = self._path[-1].fields_map[obj.name]

        if isinstance(graph_obj, Link):
            if graph_obj.type_info.type_enum is LinkType.UNION:
                self._path.append(self._graph.unions_map[graph_obj.node])
            elif graph_obj.type_info.type_enum is LinkType.INTERFACE:
                self._path.append(self._graph.interfaces_map[graph_obj.node])
            else:
                self._path.append(self._graph.nodes_map[graph_obj.node])
            try:
                node = self.visit(obj.node)
            finally:
                self._path.pop()
        else:
            assert isinstance(graph_obj, Field), type(graph_obj)
            node = obj.node

        options = (
            _get_options(self._graph, graph_obj, obj)
            if graph_obj.options
            else None
        )
        return obj.copy(node=node, options=options)


@dataclasses.dataclass
class FieldInfo:
    graph_field: Field
    query_field: Union[QueryField, QueryLink]


@dataclasses.dataclass
class LinkInfo:
    graph_link: Link
    query_link: QueryLink


class SplitQuery(QueryVisitor):
    """Splits query into two groups: fields and links.
    This is needed because we execute fields and links separately.
    """

    def __init__(self, graph_node: Node) -> None:
        self._node = graph_node
        self._fields: List[Tuple[Callable, FieldInfo]] = []
        self._links: List[LinkInfo] = []

    def split(
        self, query_node: QueryNode
    ) -> Tuple[List[Tuple[Callable, FieldInfo]], List[LinkInfo]]:
        for item in query_node.fields:
            self.visit(item)

        for fr in query_node.fragments:
            # node fragments can have different type_names
            # if node is union or inteface
            if fr.type_name == self._node.name:
                self.visit(fr)

        return self._fields, self._links

    def visit_fragment(self, obj: Fragment) -> None:
        self.visit(obj.node)

    def visit_node(self, obj: QueryNode) -> None:
        for item in obj.fields:
            self.visit(item)

    def visit_field(self, obj: QueryField) -> None:
        if obj.name == "__typename":
            return

        graph_obj = self._node.fields_map[obj.name]
        func = getattr(graph_obj.func, "__subquery__", graph_obj.func)
        self._fields.append((func, FieldInfo(graph_obj, obj)))

    def visit_link(self, obj: QueryLink) -> None:
        graph_obj = self._node.fields_map[obj.name]
        if isinstance(graph_obj, Link):
            if graph_obj.requires:
                if isinstance(graph_obj.requires, list):
                    for r in graph_obj.requires:
                        self.visit(QueryField(r))
                else:
                    self.visit(QueryField(graph_obj.requires))
            self._links.append(LinkInfo(graph_link=graph_obj, query_link=obj))
        else:
            assert isinstance(graph_obj, Field), type(graph_obj)
            # `obj` here is a link, but this link is treated as a complex field
            func = getattr(graph_obj.func, "__subquery__", graph_obj.func)
            self._fields.append((func, FieldInfo(graph_obj, obj)))


class GroupQuery(QueryVisitor):
    def __init__(self, node: Node) -> None:
        self._node = node
        self._funcs: List[Callable] = []
        self._groups: List[Union[List[FieldInfo], LinkInfo]] = []
        self._current_func = None

    def group(
        self, node: QueryNode
    ) -> List[Tuple[Callable, Union[List[FieldInfo], LinkInfo]]]:
        for item in node.fields:
            self.visit(item)
        return list(zip(self._funcs, self._groups))

    def visit_node(self, obj: QueryNode) -> NoReturn:
        raise ValueError("Unexpected value: {!r}".format(obj))

    def visit_field(self, obj: QueryField) -> None:
        graph_obj = self._node.fields_map[obj.name]
        func = getattr(graph_obj.func, "__subquery__", graph_obj.func)
        if func == self._current_func:
            assert isinstance(self._groups[-1], list)
            self._groups[-1].append(FieldInfo(graph_obj, obj))
        else:
            self._groups.append([FieldInfo(graph_obj, obj)])
            self._funcs.append(func)
            self._current_func = func

    def visit_link(self, obj: QueryLink) -> None:
        graph_obj = self._node.fields_map[obj.name]
        if graph_obj.requires:
            if isinstance(graph_obj.requires, list):
                for r in graph_obj.requires:
                    self.visit(QueryField(r))
            else:
                self.visit(QueryField(graph_obj.requires))
        self._groups.append(LinkInfo(graph_obj, obj))
        self._funcs.append(graph_obj.func)
        self._current_func = None


def _check_store_fields(
    node: Node,
    fields: List[Union[QueryField, QueryLink]],
    ids: Optional[Any],
    result: Any,
) -> None:
    if node.name is not None:
        assert ids is not None
        if (
            isinstance(result, Sequence)
            and len(result) == len(ids)
            and all(
                isinstance(r, Sequence) and len(r) == len(fields)
                for r in result
            )
        ):
            return
        else:
            expected = "list (len: {}) of lists (len: {})".format(
                len(ids), len(fields)
            )
    else:
        if isinstance(result, Sequence) and len(result) == len(fields):
            return
        else:
            expected = "list (len: {})".format(len(fields))
    raise TypeError(
        "Can't store field values, node: {!r}, fields: {!r}, "
        "expected: {}, returned: {!r}".format(
            node.name or "__root__", [f.name for f in fields], expected, result
        )
    )


def _is_hashable(obj: Any) -> bool:
    if not isinstance(obj, Hashable):
        return False

    try:
        hash(obj)
    except TypeError:
        return False

    return True


def update_index(
    index: Index,
    node: Node,
    ids: List,
    entries: List[Dict],
) -> None:
    """Update index with data from cache"""
    for idx, entry in zip(ids, entries):
        for node_name, data in entry.items():
            if node_name == node.name:
                index[node.name][idx].update(data)
            else:
                for i, row in data.items():
                    index[node_name][i].update(row)


def store_fields(
    index: Index,
    node: Node,
    query_fields: List[Union[QueryField, QueryLink]],
    ids: Optional[Any],
    query_result: Any,
) -> None:
    if inspect.isgenerator(query_result):
        warnings.warn(
            "Data loading functions should not return generators",
            DeprecationWarning,
        )
        query_result = list(query_result)

    _check_store_fields(node, query_fields, ids, query_result)

    names = [f.index_key for f in query_fields]
    if node.name is not None:
        assert ids is not None
        node_idx = index[node.name]
        for i, row in zip(ids, query_result):
            node_idx[i].update(zip(names, row))
    else:
        assert ids is None
        index.root.update(zip(names, query_result))

    return None


Req = TypeVar("Req")


def link_reqs(
    index: Index, node: Node, link: Link, ids: Any
) -> Union[List[ImmutableDict[str, Req]], List[Req], Req]:
    """For a given link, find link `requires` values by ids."""
    if node.name is not None:
        assert ids is not None
        node_idx = index[node.name]

        if isinstance(link.requires, list):
            reqs: List[ImmutableDict[str, Req]] = []
            for i in ids:
                req: ImmutableDict = ImmutableDict(
                    (r, node_idx[i][r]) for r in link.requires
                )
                reqs.append(req)
            return reqs

        return [node_idx[i][link.requires] for i in ids]
    else:
        # TODO(mkind): add support for requires as list in root node
        return index.root[link.requires]


def link_ref_maybe(graph_link: Link, ident: Any) -> Optional[Reference]:
    if ident is Nothing:
        return None
    else:
        if graph_link.type_info.type_enum in (
            LinkType.UNION,
            LinkType.INTERFACE,
        ):
            return Reference(ident[1].__type_name__, ident[0])
        return Reference(graph_link.node, ident)


def link_ref_one(graph_link: Link, ident: Any) -> Reference:
    assert ident is not Nothing

    if graph_link.type_info.type_enum in (LinkType.UNION, LinkType.INTERFACE):
        return Reference(ident[1].__type_name__, ident[0])
    return Reference(graph_link.node, ident)


def link_ref_many(graph_link: Link, idents: List) -> List[Reference]:
    if graph_link.type_info.type_enum in (LinkType.UNION, LinkType.INTERFACE):
        return [Reference(i[1].__type_name__, i[0]) for i in idents]
    return [Reference(graph_link.node, i) for i in idents]


def link_ref_maybe_many(
    graph_link: Link, idents: List
) -> List[Optional[Reference]]:
    if graph_link.type_info.type_enum in (LinkType.UNION, LinkType.INTERFACE):
        return [
            Reference(i[1].__type_name__, i[0]) if i is not Nothing else None
            for i in idents
        ]
    return [
        Reference(graph_link.node, i) if i is not Nothing else None
        for i in idents
    ]


_LINK_REF_MAKER: Dict[Any, Callable] = {
    Maybe: link_ref_maybe,
    One: link_ref_one,
    Many: link_ref_many,
    MaybeMany: link_ref_maybe_many,
}


HASH_HINT = "\nHint: Consider adding __hash__ method or use hashable type for '{!r}'.".format  # noqa: E501
SEQ_HINT = "\nHint: Consider using tuple instead of '{}'.".format
DATACLASS_FROZEN_HINT = "\nHint: Use @dataclass(frozen=True) on '{}'.".format
DATACLASS_FIELD_HINT = (
    "\nHint: Field '{}.{}' of type '{}' is not hashable.".format
)  # noqa: E501


def _hashable_hint(obj: Any) -> str:
    if isinstance(obj, (list, set)):
        return SEQ_HINT(type(obj).__name__)

    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return _hashable_hint(obj[0])

    if dataclasses.is_dataclass(obj):
        if not getattr(obj, dataclasses._PARAMS).frozen:  # type: ignore[attr-defined]  # noqa: E501
            return DATACLASS_FROZEN_HINT(obj.__class__.__name__)

        for f in dataclasses.fields(obj):
            val = getattr(obj, f.name)
            if not _is_hashable(val):
                return DATACLASS_FIELD_HINT(
                    obj.__class__.__name__, f.name, type(val).__name__
                )

    return HASH_HINT(obj)


def _check_store_links(node: Node, link: Link, ids: Any, result: Any) -> None:
    hint = ""
    if node.name is not None and link.requires is not None:
        assert ids is not None
        if link.type_enum is Maybe or link.type_enum is One:
            if isinstance(result, Sequence) and len(result) == len(ids):
                if all(map(_is_hashable, result)):
                    return
                expected = "list of hashable objects"
                hint = _hashable_hint(result)
            else:
                expected = "list (len: {})".format(len(ids))
        elif link.type_enum is Many or link.type_enum is MaybeMany:
            if (
                isinstance(result, Sequence)
                and len(result) == len(ids)
                and all(isinstance(r, Sequence) for r in result)
            ):
                unhashable = False
                for items in result:
                    if not all(map(_is_hashable, items)):
                        unhashable = True
                        break

                if not unhashable:
                    return
                expected = "list (len: {}) of lists of hashable objects".format(
                    len(ids)
                )  # noqa: E501
                hint = _hashable_hint(result)
            else:
                expected = "list (len: {}) of lists".format(len(ids))
        else:
            raise TypeError(link.type_enum)
    else:
        if link.type_enum is Maybe or link.type_enum is One:
            if _is_hashable(result):
                return
            expected = "hashable object"
            hint = _hashable_hint(result)
        elif link.type_enum is Many:
            if isinstance(result, Sequence):
                if all(map(_is_hashable, result)):
                    return
                expected = "list of hashable objects"
                hint = _hashable_hint(result)
            else:
                expected = "list"
        elif link.type_enum is MaybeMany:
            if isinstance(result, Sequence):
                if all(map(_is_hashable, result)):
                    return
                expected = "list of hashable objects and Nothing"
                hint = _hashable_hint(result)
            else:
                expected = "list"
        else:
            raise TypeError(link.type_enum)
    raise TypeError(
        "Can't store link values, node: {!r}, link: {!r}, "
        "expected: {}, returned: {!r}{}".format(
            node.name or "__root__", link.name, expected, result, hint
        )
    )


def store_links(
    index: Index,
    node: Node,
    graph_link: Link,
    query_link: QueryLink,
    ids: Any,
    query_result: Any,
) -> None:
    _check_store_links(node, graph_link, ids, query_result)

    field_val: Callable = _LINK_REF_MAKER[graph_link.type_enum]
    if node.name is not None:
        assert ids is not None
        if graph_link.requires is None:
            query_result = repeat(query_result, len(ids))

        node_idx = index[node.name]
        for i, res in zip(ids, query_result):
            node_idx[i][query_link.index_key] = field_val(graph_link, res)
    else:
        index.root[query_link.index_key] = field_val(graph_link, query_result)

    return None


def link_result_to_ids(
    from_list: bool, link_type: Any, result: Any
) -> List:  # Const
    if from_list:
        if link_type is Maybe:
            return [i for i in result if i is not Nothing]
        elif link_type is One:
            if any(i is Nothing for i in result):
                raise TypeError(
                    "Non-optional link should not return Nothing: "
                    "{!r}".format(result)
                )
            return result
        elif link_type is Many or link_type is MaybeMany:
            return list(chain.from_iterable(result))
    else:
        if link_type is Maybe:
            return [] if result is Nothing else [result]
        elif link_type is One:
            if result is Nothing:
                raise TypeError("Non-optional link should not return Nothing")
            return [result]
        elif link_type is Many or link_type is MaybeMany:
            return result
    raise TypeError(repr([from_list, link_type]))


Dep = Union[SubmitRes, TaskSet]


class Query(Workflow):
    def __init__(
        self,
        queue: Queue,
        task_set: TaskSet,
        graph: Graph,
        query: QueryNode,
        ctx: "Context",
        cache: Optional[CacheInfo] = None,
    ) -> None:
        self._queue = queue
        self._task_set = task_set
        self._graph = graph
        self._query = query
        self._ctx = ctx
        self._index = Index()
        self._cache = cache
        self._in_progress: DefaultDict = defaultdict(int)
        self._done_callbacks: DefaultDict = defaultdict(list)
        self._path_callback: Dict[Tuple, Callable] = {}

    def _track(self, path: NodePath) -> None:
        self._in_progress[path] += 1

    def _add_done_callback(self, path: NodePath, callback: Callable) -> None:
        self._done_callbacks[path].append(callback)

    def _untrack(self, path: NodePath) -> None:
        assert self._in_progress[path] > 0, f"Path {path} is already done"
        self._in_progress[path] -= 1
        if self._is_done(path):
            for callback in self._done_callbacks[path]:
                callback()

            parent_path = path[:-1]
            if parent_path in self._path_callback:
                self._path_callback[parent_path]()

    def _is_done(self, path: NodePath) -> bool:
        return self._in_progress[path] == 0

    def _submit(self, func: Callable, *args: Any, **kwargs: Any) -> SubmitRes:
        if _do_pass_context(func):
            return self._task_set.submit(func, self._ctx, *args, **kwargs)
        else:
            return self._task_set.submit(func, *args, **kwargs)

    def start(self) -> None:
        self.process_node(tuple(), self._graph.root, self._query, None)

    def result(self) -> Proxy:
        self._index.finish()
        return Proxy(self._index, ROOT, self._query)

    def _process_node_ordered(
        self, path: NodePath, node: Node, query: QueryNode, ids: Any
    ) -> None:
        proc_steps = GroupQuery(node).group(query)

        # recursively and sequentially schedule fields and links
        def proc(
            steps: List[Tuple[Callable, Union[List[FieldInfo], LinkInfo]]]
        ) -> None:
            step_func, step_item = steps.pop(0)
            if isinstance(step_item, list):
                self._track(path)
                dep = self._schedule_fields(
                    path, node, step_func, step_item, ids
                )
            else:
                self._track(path)
                dep = self._schedule_link(
                    path, node, step_item.graph_link, step_item.query_link, ids
                )

            if steps:
                self._queue.add_callback(dep, lambda: proc(steps))

        if proc_steps:
            proc(proc_steps)

    def process_node(
        self,
        path: NodePath,
        node: Node,
        query: QueryNode,
        ids: Any,
    ) -> None:
        path = path + (node.name,)
        self._path_callback[path] = lambda: self._untrack(path)

        if query.ordered:
            self._process_node_ordered(path, node, query, ids)
            return

        fields, links = SplitQuery(node).split(query)

        to_func: Dict[str, Callable] = {}
        from_func: DefaultDict[Callable, List[FieldInfo]] = defaultdict(list)
        for func, field_info in fields:
            to_func[field_info.graph_field.name] = func
            from_func[func].append(field_info)

        to_dep: Dict[Callable, Dep] = {}
        for func, func_fields_info in from_func.items():
            self._track(path)
            to_dep[func] = self._schedule_fields(
                path, node, func, func_fields_info, ids
            )

        # schedule link resolve
        for link_info in links:
            graph_link = link_info.graph_link
            link = link_info.query_link

            self._track(path)
            schedule = partial(
                self._schedule_link,
                path,
                node,
                graph_link,
                link,
                ids,
            )
            if graph_link.requires:
                if isinstance(graph_link.requires, list):
                    done_link_deps: Set = set()

                    def add_done_dep_callback(
                        done_deps: Set,
                        dep: Dep,
                        req: Any,
                        graph_link: Link,
                        schedule: Callable,
                    ) -> None:
                        def done_cb() -> None:
                            done_deps.add(req)
                            if done_deps == set(graph_link.requires):
                                schedule()

                        self._queue.add_callback(dep, done_cb)

                    for req in graph_link.requires:
                        add_done_dep_callback(
                            done_link_deps,
                            to_dep[to_func[req]],
                            req,
                            graph_link,
                            schedule,
                        )
                else:
                    dep = to_dep[to_func[graph_link.requires]]
                    self._queue.add_callback(dep, schedule)
            else:
                schedule()

    def process_link(
        self,
        path: NodePath,
        node: Node,
        graph_link: Link,
        query_link: QueryLink,
        ids: Any,
        result: List,
    ) -> None:
        """Store Link.func result in index and Call `process_node` to schedule
        Link's fields and links"""
        if inspect.isgenerator(result):
            warnings.warn(
                "Data loading functions should not return generators",
                DeprecationWarning,
            )
            result = list(result)
        store_links(self._index, node, graph_link, query_link, ids, result)
        from_list = ids is not None and graph_link.requires is not None
        to_ids = link_result_to_ids(from_list, graph_link.type_enum, result)
        if to_ids:
            if graph_link.type_info.type_enum in (
                LinkType.UNION,
                LinkType.INTERFACE,
            ) and isinstance(to_ids, list):
                grouped_ids = defaultdict(list)
                for id_, type_ref in to_ids:
                    grouped_ids[type_ref.__type_name__].append(id_)

                for type_name, type_ids in grouped_ids.items():
                    self.process_node(
                        path,
                        self._graph.nodes_map[type_name],
                        query_link.node,
                        list(type_ids),
                    )

                # FIXME: call track len(ids) - 1 times because first track was
                #  already called by process_node for this link
                for _ in range(len(grouped_ids) - 1):
                    self._track(path)
            else:
                if graph_link.type_enum is MaybeMany:
                    to_ids = [id_ for id_ in to_ids if id_ is not Nothing]

                self.process_node(
                    path,
                    self._graph.nodes_map[graph_link.node],
                    query_link.node,
                    # TODO: you can not pass [1, Nothing] as ids
                    to_ids,
                )
        else:
            self._untrack(path)

        return None

    def _schedule_fields(
        self,
        path: NodePath,
        node: Node,
        func: Callable,
        fields_info: List[FieldInfo],
        ids: Optional[Any],
    ) -> Union[SubmitRes, TaskSet]:
        query_fields = [f.query_field for f in fields_info]

        dep: Union[TaskSet, SubmitRes]
        if hasattr(func, "__subquery__"):
            assert ids is not None
            dep = self._queue.fork(self._task_set)
            fields = [(f.graph_field, f.query_field) for f in fields_info]
            proc = func(fields, ids, self._queue, self._ctx, dep)
        else:
            if ids is None:
                dep = self._submit(func, query_fields)
            else:
                dep = self._submit(func, query_fields, ids)
            proc = dep.result

        def callback() -> None:
            store_fields(
                self._index,
                node,
                query_fields,
                ids,
                proc(),
            )
            self._untrack(path)

        self._queue.add_callback(dep, callback)
        return dep

    def _update_index_from_cache(
        self,
        path: NodePath,
        node: Node,
        graph_link: Link,
        query_link: QueryLink,
        ids: List[Any],
        reqs: List[Any],
    ) -> SubmitRes:
        assert self._cache is not None
        key_info = []
        for i, req in zip(ids, reqs):
            key_info.append(
                (self._cache.query_hash(self._ctx, query_link, req), i, req)
            )

        keys = set(info[0] for info in key_info)
        dep = self._submit(
            self._cache.get_many, list(keys), node.name, graph_link.name
        )

        def callback() -> None:
            result = dep.result()
            cached_data = []
            cached_ids = []
            for key, i, req in key_info:
                if key in result:
                    cached_ids.append(i)
                    cached_data.append(result[key])

            nonlocal ids
            if cached_data:
                update_index(self._index, node, cached_ids, cached_data)
                ids = [i for i in ids if i not in cached_ids]

            if ids:
                self._schedule_link(
                    path,
                    node,
                    graph_link,
                    query_link,
                    ids,
                    skip_cache=True,
                )

        self._queue.add_callback(dep, callback)
        return dep

    def _schedule_link(
        self,
        path: NodePath,
        node: Node,
        graph_link: Link,
        query_link: QueryLink,
        ids: Any,
        skip_cache: bool = False,
    ) -> SubmitRes:
        """Schedules link (submits Link.func to executor).

        If link has `requires` specified, take required values list from index
        and pass it as first argument to link.func.

        If link has `options`, pass as a first argument if `requires` not
        provided or as second if `requires` provided.

        When Link.func is executed by executor, a `process_link`
        method called with result.
        """
        args = []
        if graph_link.requires:
            # collect data for link requires from store
            reqs: Any = link_reqs(self._index, node, graph_link, ids)

            if (
                "cached" in query_link.directives_map
                and self._cache
                and not skip_cache
            ):
                return self._update_index_from_cache(
                    path, node, graph_link, query_link, ids, reqs
                )

            args.append(reqs)

        if graph_link.options:
            args.append(query_link.options)

        dep = self._submit(graph_link.func, *args)

        def callback() -> None:
            return self.process_link(
                path,
                node,
                graph_link,
                query_link,
                ids,
                dep.result(),
            )

        self._queue.add_callback(dep, callback)

        def store_link_cache() -> None:
            assert self._cache is not None
            cached = query_link.directives_map["cached"]
            reqs: Any = link_reqs(self._index, node, graph_link, ids)
            to_cache = CacheVisitor(
                self._cache, self._index, self._graph, node
            ).process(query_link, ids, reqs, self._ctx)

            self._submit(self._cache.set_many, to_cache, cached.ttl)

        if "cached" in query_link.directives_map and self._cache:
            self._add_done_callback(path + (graph_link.node,), store_link_cache)

        return dep


R = TypeVar("R")
P = ParamSpec("P")


def pass_context(
    func: Callable[P, R]
) -> Callable[Concatenate["Context", P], R]:
    """Decorator to pass context to a function as a first argument.

    Can be used on functions for ``Field`` and ``Link``.
    Can not be used on functions with ``@define`` decorator
    """
    func.__pass_context__ = True  # type: ignore[attr-defined]
    return cast(Callable[Concatenate["Context", P], R], func)


def _do_pass_context(func: Callable) -> bool:
    return getattr(func, "__pass_context__", False)


class Context(Mapping):
    def __init__(self, mapping: Mapping) -> None:
        self.__mapping = mapping

    def __len__(self) -> int:
        return len(self.__mapping)

    def __iter__(self) -> Iterator:
        return iter(self.__mapping)

    def __getitem__(self, item: Any) -> Any:
        try:
            return self.__mapping[item]
        except KeyError:
            raise KeyError(
                "Key {!r} is not specified " "in the query context".format(item)
            )


# Covariant must be used because we want to accept subclasses of Executor
_ExecutorType = TypeVar(
    "_ExecutorType", covariant=True, bound=SyncAsyncExecutor
)


class Engine(Generic[_ExecutorType]):
    executor: _ExecutorType

    def __init__(
        self,
        executor: _ExecutorType,
        cache: Optional[CacheSettings] = None,
    ) -> None:
        self.executor = executor
        self.cache_settings = cache

    def _prepare_workflow(
        self, execution_context: ExecutionContext
    ) -> Tuple[Queue, Query]:
        graph = execution_context.graph
        query = execution_context.query
        ctx = execution_context.context
        operation_name = execution_context.operation_name

        query = InitOptions(graph).visit(query)
        assert query is not None
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        cache = (
            CacheInfo(
                self.cache_settings,
                operation_name,
            )
            if self.cache_settings
            else None
        )
        query_workflow = Query(
            queue, task_set, graph, query, Context(ctx), cache
        )
        query_workflow.start()
        return queue, query_workflow

    @overload
    async def execute(
        self: "Engine[BaseAsyncExecutor]",
        execution_context: ExecutionContext,
    ) -> Proxy: ...

    @overload
    def execute(
        self: "Engine[BaseSyncExecutor]",
        execution_context: ExecutionContext,
    ) -> Proxy: ...

    def execute(
        self,
        execution_context: ExecutionContext,
    ) -> Any:
        queue, workflow = self._prepare_workflow(execution_context)
        return self.executor.process(queue, workflow)
