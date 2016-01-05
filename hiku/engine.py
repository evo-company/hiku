from functools import partial
from itertools import chain
from collections import defaultdict

from .edn import Keyword, Dict
from .graph import Link, Edge
from .store import Store
from .executors.queue import Workflow, Queue


def edge_split(edge, pattern):
    fields = []
    links = []

    for item in pattern:
        if isinstance(item, Keyword):
            fields.append(edge.fields[item])
        elif isinstance(item, Dict):
            for key, value in item.items():
                field = edge.fields[key]
                if isinstance(field, Link):
                    if field.requires:
                        fields.append(edge.fields[field.requires])
                    links.append((field, value))
                elif isinstance(field, Edge):
                    _fields, _links = edge_split(field, value)
                    fields.extend(_fields)
                    links.extend(_links)
                else:
                    raise ValueError('Unexpected name: {}'.format(key))
        else:
            raise ValueError('Unexpected value: {!r}'.format(item))

    return fields, links


def store_fields(store, edge, fields, ids, result):
    names = [f.name for f in fields]
    if edge.name is not None:
        if ids is not None:
            for i, row in zip(ids, result):
                store[edge.name][i].update(zip(names, row))
        else:
            store[edge.name].update(zip(names, result))
    else:
        store.update(zip(names, result))


def link_reqs(store, edge, link, ids):
    if edge.name is not None:
        if ids is not None:
            return [store[edge.name][i][link.requires] for i in ids]
        else:
            return store[edge.name][link.requires]
    else:
        return store[link.requires]


def link_ref(store, link, ident):
    return store.ref(link.entity, ident)


def link_refs(store, link, idents):
    return [store.ref(link.entity, i) for i in idents]


def store_links(store, edge, link, ids, result):
    field_val = partial(link_refs if link.to_list else link_ref,
                        store, link)
    if edge.name is not None:
        if ids is not None:
            for i, res in zip(ids, result):
                store[edge.name][i][link.name] = field_val(res)
        else:
            store[edge.name][link.name] = field_val(result)
    else:
        store[link.name] = field_val(result)


def link_result_to_ids(is_list, to_list, result):
    if is_list and to_list:
        return list(chain.from_iterable(result))
    elif is_list or to_list:
        return result
    else:
        return [result]


class Query(Workflow):

    def __init__(self, queue, task_set, root, pattern):
        self._queue = queue
        self._task_set = task_set
        self.root = root
        self.pattern = pattern
        self.store = Store()

    def begin(self):
        self._process_edge(self.root, self.pattern, None)

    def result(self):
        return self.store

    def _process_edge(self, edge, pattern, ids):
        fields, links = edge_split(edge, pattern)

        to_func = {}
        from_func = defaultdict(list)
        for field in fields:
            to_func[field.name] = field.func
            from_func[field.func].append(field.name)

        # schedule fields resolve
        to_fut = {}
        for func, names in from_func.items():
            if ids is not None:
                fut = self._task_set.submit(func, names, ids)
            else:
                fut = self._task_set.submit(func, names)
            to_fut[func] = fut
            self._queue.add_callback(fut, (
                lambda result:
                store_fields(self.store, edge, fields, ids, result)
            ))

        # schedule link resolve
        for link, link_pattern in links:
            if link.requires:
                fut = to_fut[to_func[link.requires]]
                self._queue.add_callback(fut, (
                    lambda _:
                    self._process_edge_link(edge, link, link_pattern, ids)
                ))
            else:
                fut = self._task_set.submit(link.func)
                self._queue.add_callback(fut, (
                    lambda result:
                    self._process_link(edge, link, link_pattern, ids, result)
                ))

    def _process_edge_link(self, edge, link, link_pattern, ids):
        reqs = link_reqs(self.store, edge, link, ids)
        fut = self._task_set.submit(link.func, reqs)
        self._queue.add_callback(fut, (
            lambda result:
            self._process_link(edge, link, link_pattern, ids, result)
        ))

    def _process_link(self, edge, link, link_pattern, ids, result):
        store_links(self.store, edge, link, ids, result)
        to_ids = link_result_to_ids(ids is not None, link.to_list, result)
        self._process_edge(self.root.fields[link.entity], link_pattern,
                           to_ids)


class Engine(object):

    def __init__(self, executor):
        self.executor = executor

    def execute(self, root, pattern):
        queue = Queue(self.executor)
        task_set = queue.fork()
        query = Query(queue, task_set, root, pattern)
        query.begin()
        return self.executor.process(queue, query)
