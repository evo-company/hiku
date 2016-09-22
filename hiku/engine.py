from functools import partial
from itertools import chain
from collections import defaultdict

from . import query
from .graph import Link, Edge, Maybe, One, Many, Nothing, Field
from .result import Result
from .executors.queue import Workflow, Queue


class SplitPattern(query.QueryVisitor):

    def __init__(self, edge):
        self._edge = edge
        self._fields = []
        self._links = []
        self._edges = []

    def split(self, pattern):
        for item in pattern.fields:
            self.visit(item)
        return self._fields, self._links, self._edges

    def visit_edge(self, node):
        raise ValueError('Unexpected value: {!r}'.format(node))

    def visit_field(self, node):
        self._fields.append((self._edge.fields_map[node.name], node))

    def visit_link(self, node):
        obj = self._edge.fields_map[node.name]
        if isinstance(obj, Link):
            if obj.requires:
                self._fields.append((self._edge.fields_map[obj.requires],
                                     query.Field(obj.requires)))
            self._links.append((obj, node))
        elif isinstance(obj, Edge):
            self._edges.append(node)
        else:
            assert isinstance(obj, Field), type(obj)
            # `node` here is a link, but this link is treated as a complex field
            self._fields.append((obj, node))


def store_fields(result, edge, fields, ids, query_result):
    names = [f.name for f in fields]
    if edge.name is not None:
        if ids is not None:
            for i, row in zip(ids, query_result):
                result.index[edge.name][i].update(zip(names, row))
        else:
            result[edge.name].update(zip(names, query_result))
    else:
        result.update(zip(names, query_result))


def link_reqs(result, edge, link, ids):
    if edge.name is not None:
        if ids is not None:
            return [result.index[edge.name][i][link.requires] for i in ids]
        else:
            return result[edge.name][link.requires]
    else:
        return result[link.requires]


def link_ref_maybe(result, link, ident):
    return None if ident is Nothing else result.ref(link.edge, ident)


def link_ref_one(result, link, ident):
    assert ident is not Nothing
    return result.ref(link.edge, ident)


def link_ref_many(result, link, idents):
    return [result.ref(link.edge, i) for i in idents]


_LINK_REF_MAKER = {
    Maybe: link_ref_maybe,
    One: link_ref_one,
    Many: link_ref_many,
}


def store_links(result, edge, link, ids, query_result):
    field_val = partial(_LINK_REF_MAKER[link.type_enum], result, link)
    if edge.name is not None:
        if ids is not None:
            for i, res in zip(ids, query_result):
                result.index[edge.name][i][link.name] = field_val(res)
        else:
            result[edge.name][link.name] = field_val(query_result)
    else:
        result[link.name] = field_val(query_result)


def link_result_to_ids(is_list, link_type, result):
    if is_list:
        if link_type is Maybe:
            return [i for i in result if i is not Nothing]
        elif link_type is One:
            assert all(i is not Nothing for i in result)
            return result
        elif link_type is Many:
            return list(chain.from_iterable(result))
    else:
        if link_type is Maybe:
            return [] if result is Nothing else [result]
        elif link_type is One:
            assert result is not Nothing
            return [result]
        elif link_type is Many:
            return result
    raise TypeError(repr([is_list, link_type]))


def get_options(graph_obj, query_obj):
    _options = query_obj.options or {}
    options = {}
    for opt in graph_obj.options:
        options[opt.name] = _options.get(opt.name, opt.default)
    return options


class Query(Workflow):

    def __init__(self, queue, task_set, graph, ctx):
        self._queue = queue
        self._task_set = task_set
        self.graph = graph
        self._ctx = ctx
        self._result = Result()

    def _submit(self, func, *args, **kwargs):
        if _do_pass_context(func):
            return self._task_set.submit(func, self._ctx, *args, **kwargs)
        else:
            return self._task_set.submit(func, *args, **kwargs)

    def result(self):
        return self._result

    def process_edge(self, edge, pattern, ids):
        fields, links, edges = SplitPattern(edge).split(pattern)

        assert not (edge.name and edges), 'Nested edges are not supported yet'
        for link in edges:
            self.process_edge(edge.fields_map[link.name], link.edge, None)

        to_func = {}
        from_func = defaultdict(list)
        for graph_field, query_field in fields:
            to_func[graph_field.name] = graph_field.func
            from_func[graph_field.func].append(query_field)

        # schedule fields resolve
        to_fut = {}
        for func, func_fields in from_func.items():
            if _is_subquery(func):
                task_set = self._queue.fork(self._task_set)
                if ids is not None:
                    result_proc = func(self._queue, self._ctx, task_set,
                                       edge, func_fields, ids)
                else:
                    result_proc = func(self._queue, self._ctx, task_set,
                                       edge, func_fields)
                to_fut[func] = task_set
                self._queue.add_callback(task_set, (
                    lambda:
                    result_proc(self._result)
                ))
            else:
                if ids is not None:
                    fut = self._submit(func, func_fields, ids)
                else:
                    fut = self._submit(func, func_fields)
                to_fut[func] = fut
                self._queue.add_callback(fut, (
                    lambda _fut=fut, _func_fields=func_fields:
                    store_fields(self._result, edge, _func_fields, ids,
                                 _fut.result())
                ))

        # schedule link resolve
        for graph_link, query_link in links:
            if graph_link.requires:
                fut = to_fut[to_func[graph_link.requires]]
                self._queue.add_callback(fut, (
                    lambda _gl=graph_link, _ql=query_link:
                    self._process_edge_link(edge, _gl, _ql, ids)
                ))
            else:
                if graph_link.options:
                    options = get_options(graph_link, query_link)
                    fut = self._submit(graph_link.func, options)
                else:
                    fut = self._submit(graph_link.func)
                self._queue.add_callback(fut, (
                    lambda _fut=fut, _gl=graph_link, _qe=query_link.edge:
                    self.process_link(edge, _gl, _qe, ids, _fut.result())
                ))

    def _process_edge_link(self, edge, graph_link, query_link, ids):
        reqs = link_reqs(self._result, edge, graph_link, ids)
        if graph_link.options:
            options = get_options(graph_link, query_link)
            fut = self._submit(graph_link.func, reqs, options)
        else:
            fut = self._submit(graph_link.func, reqs)
        self._queue.add_callback(fut, (
            lambda:
            self.process_link(edge, graph_link, query_link.edge, ids,
                              fut.result())
        ))

    def process_link(self, edge, graph_link, query_edge, ids, result):
        store_links(self._result, edge, graph_link, ids, result)
        to_ids = link_result_to_ids(ids is not None, graph_link.type_enum,
                                    result)
        if to_ids:
            self.process_edge(self.graph.edges_map[graph_link.edge], query_edge,
                              to_ids)


def pass_context(func):
    func.__pass_context__ = True
    return func


def _do_pass_context(func):
    return getattr(func, '__pass_context__', False)


def subquery(func):
    func.__subquery__ = True
    return func


def _is_subquery(func):
    return getattr(func, '__subquery__', False)


class Context(object):

    def __init__(self, mapping):
        self.__mapping = mapping

    def __getitem__(self, item):
        try:
            return self.__mapping[item]
        except KeyError:
            raise KeyError('Context variable {!r} is not specified '
                           'in the query context'.format(item))


class Engine(object):

    def __init__(self, executor):
        self.executor = executor

    def execute(self, graph, pattern, ctx=None):
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        q = Query(queue, task_set, graph, Context(ctx or {}))
        q.process_edge(q.graph.root, pattern, None)
        return self.executor.process(queue, q)
