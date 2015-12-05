from itertools import chain
from collections import defaultdict

from .edn import Keyword, Dict
from .graph import Link
from .store import Store
from .reader import read


class Query(object):

    def __init__(self, executor, env, edge_name, fields, ids):
        self.executor = executor
        self.env = env
        self.edge_name = edge_name
        self.fields = fields
        self.ids = ids

        self.store = Store()
        self.futures = set()
        self.callbacks = defaultdict(list)

    def begin(self):
        self._process_edge(self.edge_name, self.fields, self.ids)

    def _store_rows(self, fut_result, edge_name, names, ids):
        for row_id, row in zip(ids, fut_result):
            self.store.update(edge_name, row_id, zip(names, row))

    def _store_links(self, fut_result, edge, link_name, requirements):
        link = edge.fields[link_name]
        if link.is_list:
            for from_id, to_ids in zip(requirements, fut_result):
                self.store.update(edge.name, from_id,
                                  [(link_name,
                                    [self.store.ref(link.entity, i)
                                     for i in to_ids])])
        else:
            for from_id, to_id in zip(requirements, fut_result):
                self.store.update(edge.name, from_id,
                                  [(link_name,
                                    self.store.ref(link.entity, to_id))])

    def _process_linked_edge(self, fut_result, link, fields):
        if link.is_list:
            to_ids = list(chain.from_iterable(fut_result))
        else:
            to_ids = fut_result
        self._process_edge(link.entity, fields, to_ids)

    def _process_link(self, fut_result, edge, link_name, fields, ids):
        link = edge.fields[link_name]
        reqs = [self.store.ref(edge.name, i)[link.requires] for i in ids]
        fut = self.executor.submit(link.func, reqs)
        self.futures.add(fut)
        self.callbacks[fut].append((self._store_links, edge, link_name, reqs))
        self.callbacks[fut].append((self._process_linked_edge, link, fields))

    def _process_edge(self, edge_name, fields, ids):
        edge = self.env[edge_name]

        field_names = []
        links = []

        for field in fields:
            if isinstance(field, Keyword):
                field_names.append(field)
            elif isinstance(field, Dict):
                for key, value in field.items():
                    field_names.append(key)
                    # TODO: some links can be queried in parallel
                    # with current edge
                    links.append((edge.name, key, value))
            else:
                raise TypeError(type(field))

        mapping = defaultdict(list)
        for field_name in field_names:
            field = edge.fields[field_name]
            if isinstance(field, Link):
                field = edge.fields[field.requires]
            mapping[field.func].append(field.name)

        name_to_fut = {}
        for func, names in mapping.items():
            fut = self.executor.submit(func, names, ids)
            self.futures.add(fut)
            self.callbacks[fut]\
                .append((self._store_rows, edge.name, names, ids))
            for name in names:
                name_to_fut[name] = fut

        for edge_name, link_name, fields in links:
            edge = self.env[edge_name]
            link = edge.fields[link_name]
            fut = name_to_fut[link.requires]
            self.callbacks[fut].append((self._process_link, edge, link_name,
                                        fields, ids))

    def progress(self, futures):
        for fut in futures:
            for cb_tuple in self.callbacks[fut]:
                fn, args = cb_tuple[0], cb_tuple[1:]
                fn(fut.result(), *args)
            self.futures.remove(fut)

    def result(self):
        return [self.store.ref(self.edge_name, ident) for ident in self.ids]


class Engine(object):

    def __init__(self, env, executor):
        self.env = env
        self.executor = executor

    def execute(self, pattern, ids):
        pattern = read(pattern)
        (edge_name, fields), = pattern.items()
        query = Query(self.executor, self.env, edge_name, fields, ids)
        return self.executor.process(query)
