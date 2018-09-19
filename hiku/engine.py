import inspect

from functools import partial
from itertools import chain, repeat
from collections import defaultdict, Sequence

from . import query as hiku_query
from .graph import Link, Maybe, One, Many, Nothing, Field
from .result import Proxy, Index, ROOT, Reference
from .executors.queue import Workflow, Queue


def _yield_options(graph_obj, query_obj):
    options = query_obj.options or {}
    for option in graph_obj.options:
        value = options.get(option.name, option.default)
        if value is Nothing:
            raise TypeError('Required option "{}" for {!r} was not provided'
                            .format(option.name, graph_obj))
        else:
            yield option.name, value


def _get_options(graph_obj, query_obj):
    return dict(_yield_options(graph_obj, query_obj))


class InitOptions(hiku_query.QueryVisitor):

    def __init__(self, graph):
        self._graph = graph
        self._path = [graph.root]

    def visit_field(self, obj):
        graph_obj = self._path[-1].fields_map[obj.name]
        if graph_obj.options:
            options = _get_options(graph_obj, obj)
            return hiku_query.Field(obj.name, options=options, alias=obj.alias)
        else:
            return obj

    def visit_link(self, obj):
        graph_obj = self._path[-1].fields_map[obj.name]

        if isinstance(graph_obj, Link):
            self._path.append(self._graph.nodes_map[graph_obj.node])
            try:
                node = self.visit(obj.node)
            finally:
                self._path.pop()
        else:
            assert isinstance(graph_obj, Field), type(graph_obj)
            node = obj.node

        options = _get_options(graph_obj, obj) if graph_obj.options else None
        return hiku_query.Link(obj.name, node, options=options, alias=obj.alias)

    def visit_node(self, obj):
        return hiku_query.Node([self.visit(f) for f in obj.fields])


class SplitQuery(hiku_query.QueryVisitor):

    def __init__(self, node):
        self._node = node
        self._fields = []
        self._links = []

    def split(self, node):
        for item in node.fields:
            self.visit(item)
        return self._fields, self._links

    def visit_node(self, obj):
        raise ValueError('Unexpected value: {!r}'.format(obj))

    def visit_field(self, obj):
        self._fields.append((self._node.fields_map[obj.name], obj))

    def visit_link(self, obj):
        graph_obj = self._node.fields_map[obj.name]
        if isinstance(graph_obj, Link):
            if graph_obj.requires:
                self._fields.append((self._node.fields_map[graph_obj.requires],
                                     hiku_query.Field(graph_obj.requires)))
            self._links.append((graph_obj, obj))
        else:
            assert isinstance(graph_obj, Field), type(graph_obj)
            # `obj` here is a link, but this link is treated as a complex field
            self._fields.append((graph_obj, obj))


def _check_store_fields(node, fields, ids, result):
    if node.name is not None:
        assert ids is not None
        if (
            isinstance(result, Sequence)
            and len(result) == len(ids)
            and all(isinstance(r, Sequence) and len(r) == len(fields)
                    for r in result)
        ):
            return
        else:
            expected = ('list (len: {}) of lists (len: {})'
                        .format(len(ids), len(fields)))
    else:
        if isinstance(result, Sequence) and len(result) == len(fields):
            return
        else:
            expected = 'list (len: {})'.format(len(fields))
    raise TypeError('Can\'t store field values, node: {!r}, fields: {!r}, '
                    'expected: {}, returned: {!r}'
                    .format(node.name or '__root__', [f.name for f in fields],
                            expected, result))


def store_fields(index, node, query_fields, ids, query_result):
    if inspect.isgenerator(query_result):
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


def link_reqs(index, node, link, ids):
    if node.name is not None:
        assert ids is not None
        node_idx = index[node.name]
        return [node_idx[i][link.requires] for i in ids]
    else:
        return index.root[link.requires]


def link_ref_maybe(graph_link, ident):
    if ident is Nothing:
        return None
    else:
        return Reference(graph_link.node, ident)


def link_ref_one(graph_link, ident):
    assert ident is not Nothing
    return Reference(graph_link.node, ident)


def link_ref_many(graph_link, idents):
    return [Reference(graph_link.node, i) for i in idents]


_LINK_REF_MAKER = {
    Maybe: link_ref_maybe,
    One: link_ref_one,
    Many: link_ref_many,
}


def _check_store_links(node, link, ids, result):
    if node.name is not None and link.requires is not None:
        assert ids is not None
        if link.type_enum is Maybe or link.type_enum is One:
            if isinstance(result, Sequence) and len(result) == len(ids):
                return
            else:
                expected = 'list (len: {})'.format(len(ids))
        elif link.type_enum is Many:
            if (
                isinstance(result, Sequence)
                and len(result) == len(ids)
                and all(isinstance(r, Sequence) for r in result)
            ):
                return
            else:
                expected = 'list (len: {}) of lists'.format(len(ids))
        else:
            raise TypeError(link.type_enum)
    else:
        if link.type_enum is Maybe or link.type_enum is One:
            return
        elif link.type_enum is Many:
            if isinstance(result, Sequence):
                return
            else:
                expected = 'list'
        else:
            raise TypeError(link.type_enum)
    raise TypeError('Can\'t store link values, node: {!r}, link: {!r}, '
                    'expected: {}, returned: {!r}'
                    .format(node.name or '__root__', link.name,
                            expected, result))


def store_links(index, node, graph_link, query_link, ids, query_result):
    _check_store_links(node, graph_link, ids, query_result)

    field_val = partial(_LINK_REF_MAKER[graph_link.type_enum], graph_link)
    if node.name is not None:
        assert ids is not None
        if graph_link.requires is None:
            query_result = repeat(query_result, len(ids))

        node_idx = index[node.name]
        for i, res in zip(ids, query_result):
            node_idx[i][query_link.index_key] = field_val(res)
    else:
        index.root[query_link.index_key] = field_val(query_result)


def link_result_to_ids(from_list, link_type, result):
    if from_list:
        if link_type is Maybe:
            return [i for i in result if i is not Nothing]
        elif link_type is One:
            if any(i is Nothing for i in result):
                raise TypeError('Non-optional link should not return Nothing: '
                                '{!r}'.format(result))
            return result
        elif link_type is Many:
            return list(chain.from_iterable(result))
    else:
        if link_type is Maybe:
            return [] if result is Nothing else [result]
        elif link_type is One:
            if result is Nothing:
                raise TypeError('Non-optional link should not return Nothing')
            return [result]
        elif link_type is Many:
            return result
    raise TypeError(repr([from_list, link_type]))


class Query(Workflow):

    def __init__(self, queue, task_set, graph, query, ctx):
        self._queue = queue
        self._task_set = task_set
        self._graph = graph
        self._query = query
        self._ctx = ctx
        self._index = Index()

    def _submit(self, func, *args, **kwargs):
        if _do_pass_context(func):
            return self._task_set.submit(func, self._ctx, *args, **kwargs)
        else:
            return self._task_set.submit(func, *args, **kwargs)

    def start(self):
        self.process_node(self._graph.root, self._query, None)

    def result(self):
        self._index.finish()
        return Proxy(self._index, ROOT, self._query)

    def process_node(self, node, query, ids):
        fields, links = SplitQuery(node).split(query)

        to_func = {}
        from_func = defaultdict(list)
        for graph_field, query_field in fields:
            func = getattr(graph_field.func, '__subquery__', graph_field.func)
            to_func[graph_field.name] = func
            from_func[func].append((graph_field, query_field))

        # schedule fields resolve
        to_dep = {}
        for func, func_fields in from_func.items():
            query_fields = [qf for _, qf in func_fields]
            if hasattr(func, '__subquery__'):
                assert ids is not None
                dep = self._queue.fork(self._task_set)
                proc = func(func_fields, ids, self._queue, self._ctx, dep)
            else:
                if ids is None:
                    dep = self._submit(func, query_fields)
                else:
                    dep = self._submit(func, query_fields, ids)
                proc = dep.result

            to_dep[func] = dep
            self._queue.add_callback(dep, (
                lambda _query_fields=query_fields, _proc=proc:
                store_fields(self._index, node, _query_fields, ids, _proc())
            ))

        # schedule link resolve
        for graph_link, query_link in links:
            if graph_link.requires:
                dep = to_dep[to_func[graph_link.requires]]
                self._queue.add_callback(dep, (
                    lambda _gl=graph_link, _ql=query_link:
                    self._process_node_link(node, _gl, _ql, ids)
                ))
            else:
                if graph_link.options:
                    dep = self._submit(graph_link.func, query_link.options)
                else:
                    dep = self._submit(graph_link.func)
                self._queue.add_callback(dep, (
                    lambda _fut=dep, _gl=graph_link, _ql=query_link:
                    self.process_link(node, _gl, _ql, ids, _fut.result())
                ))

    def _process_node_link(self, node, graph_link, query_link, ids):
        reqs = link_reqs(self._index, node, graph_link, ids)
        if graph_link.options:
            dep = self._submit(graph_link.func, reqs, query_link.options)
        else:
            dep = self._submit(graph_link.func, reqs)
        self._queue.add_callback(dep, (
            lambda:
            self.process_link(node, graph_link, query_link, ids, dep.result())
        ))

    def process_link(self, node, graph_link, query_link, ids, result):
        if inspect.isgenerator(result):
            result = list(result)
        store_links(self._index, node, graph_link, query_link, ids, result)
        from_list = ids is not None and graph_link.requires is not None
        to_ids = link_result_to_ids(from_list, graph_link.type_enum, result)
        if to_ids:
            self.process_node(self._graph.nodes_map[graph_link.node],
                              query_link.node, to_ids)


def pass_context(func):
    func.__pass_context__ = True
    return func


def _do_pass_context(func):
    return getattr(func, '__pass_context__', False)


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

    def execute(self, graph, query, ctx=None):
        if ctx is None:
            ctx = {}
        query = InitOptions(graph).visit(query)
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        query_workflow = Query(queue, task_set, graph, query, Context(ctx))
        query_workflow.start()
        return self.executor.process(queue, query_workflow)
