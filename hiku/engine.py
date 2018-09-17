import inspect

from functools import partial
from itertools import chain, repeat
from collections import defaultdict, Sequence

from . import query
from .graph import Link, Maybe, One, Many, Nothing, Field
from .result import Reference, Proxy
from .executors.queue import Workflow, Queue


class InitOptions(query.QueryVisitor):

    def __init__(self, graph):
        self._graph = graph
        self._path = [graph.root]

    def _yield_options(self, graph_obj, query_obj):
        options = query_obj.options or {}
        for option in graph_obj.options:
            value = options.get(option.name, option.default)
            if value is Nothing:
                raise TypeError('Required option "{}" for {!r} was not provided'
                                .format(option.name, graph_obj))
            else:
                yield option.name, value

    def _get_options(self, graph_obj, query_obj):
        return dict(self._yield_options(graph_obj, query_obj))

    def visit_field(self, obj):
        graph_obj = self._path[-1].fields_map[obj.name]
        if graph_obj.options:
            options = self._get_options(graph_obj, obj)
            return query.Field(obj.name, options=options, alias=obj.alias)
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

        if graph_obj.options:
            options = self._get_options(graph_obj, obj)
        else:
            options = None
        return query.Link(obj.name, node, options=options, alias=obj.alias)

    def visit_node(self, obj):
        return query.Node([self.visit(f) for f in obj.fields])


class SplitPattern(query.QueryVisitor):

    def __init__(self, node):
        self._node = node
        self._fields = []
        self._links = []

    def split(self, pattern):
        for item in pattern.fields:
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
                                     query.Field(graph_obj.requires)))
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


def store_fields(result, node, query_fields, ids, query_result):
    if inspect.isgenerator(query_result):
        query_result = list(query_result)

    _check_store_fields(node, query_fields, ids, query_result)

    names = [f.index_key for f in query_fields]
    if node.name is not None:
        assert ids is not None
        node_idx = result.__idx__[node.name]
        for i, row in zip(ids, query_result):
            node_idx[i].update(zip(names, row))
    else:
        assert ids is None
        root = result.__idx__[Reference.ROOT][Reference.ROOT]
        root.update(zip(names, query_result))


def link_reqs(result, node, link, ids):
    if node.name is not None:
        assert ids is not None
        node_idx = result.__idx__[node.name]
        return [node_idx[i][link.requires] for i in ids]
    else:
        root = result.__idx__[Reference.ROOT][Reference.ROOT]
        return root[link.requires]


def link_ref_maybe(result, graph_link, ident):
    if ident is Nothing:
        return None
    else:
        return Reference(result.__idx__, graph_link.node, ident)


def link_ref_one(result, graph_link, ident):
    assert ident is not Nothing
    return Reference(result.__idx__, graph_link.node, ident)


def link_ref_many(result, graph_link, idents):
    return [Reference(result.__idx__, graph_link.node, i) for i in idents]


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


def store_links(result, node, graph_link, query_link, ids, query_result):
    _check_store_links(node, graph_link, ids, query_result)

    field_val = partial(_LINK_REF_MAKER[graph_link.type_enum],
                        result, graph_link)
    if node.name is not None:
        assert ids is not None
        if graph_link.requires is None:
            query_result = repeat(query_result, len(ids))

        node_idx = result.__idx__[node.name]
        for i, res in zip(ids, query_result):
            node_idx[i][query_link.index_key] = field_val(res)
    else:
        root = result.__idx__[Reference.ROOT][Reference.ROOT]
        root[query_link.index_key] = field_val(query_result)


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

    def __init__(self, queue, task_set, graph, pattern, ctx):
        self._queue = queue
        self._task_set = task_set
        self.graph = graph
        self._pattern = pattern
        self._ctx = ctx
        self._result = Reference.__root__()

    def _submit(self, func, *args, **kwargs):
        if _do_pass_context(func):
            return self._task_set.submit(func, self._ctx, *args, **kwargs)
        else:
            return self._task_set.submit(func, *args, **kwargs)

    def result(self):
        return Proxy(self._result, self._pattern)

    def process_node(self, node, pattern, ids):
        fields, links = SplitPattern(node).split(pattern)

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
                store_fields(self._result, node, _query_fields, ids, _proc())
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
        reqs = link_reqs(self._result, node, graph_link, ids)
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
        store_links(self._result, node, graph_link, query_link, ids, result)
        from_list = ids is not None and graph_link.requires is not None
        to_ids = link_result_to_ids(from_list, graph_link.type_enum, result)
        if to_ids:
            self.process_node(self.graph.nodes_map[graph_link.node],
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

    def execute(self, graph, pattern, ctx=None):
        query_ = InitOptions(graph).visit(pattern)
        queue = Queue(self.executor)
        task_set = queue.fork(None)
        q = Query(queue, task_set, graph, query_, Context(ctx or {}))
        q.process_node(q.graph.root, query_, None)
        return self.executor.process(queue, q)
