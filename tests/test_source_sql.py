from unittest import TestCase
from itertools import chain
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.edn import Keyword, Dict
from hiku.store import Store
from hiku.graph import Field, Edge, Link
from hiku.reader import read
from hiku.compat import PY3

if not PY3:
    import warnings
    from sqlalchemy.exc import SAWarning
    warnings.filterwarnings('ignore', '', SAWarning, '', 0)


metadata = MetaData()


foo_table = Table(
    'foo',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', Unicode),
    Column('count', Integer),
    Column('bar_id', ForeignKey('bar.id')),
)


bar_table = Table(
    'bar',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', Unicode),
    Column('type', Integer),
)


def _query(engine, table, attrs, idents):
    p_key, = list(table.primary_key)
    columns = [getattr(table.c, attr) for attr in attrs]
    rows = engine.execute(select([p_key] + columns)
                          .where(p_key.in_(idents))).fetchall()
    rows_map = {row[p_key]: [row[k] for k in columns] for row in rows}
    return [rows_map.get(ident) for ident in idents]


def query_foo(engine, attrs, idents):
    return _query(engine, foo_table, attrs, idents)


def query_bar(engine, attrs, idents):
    return _query(engine, bar_table, attrs, idents)


def foo_bar_link(engine, bar_ids):
    return bar_ids


def bar_foo_link(engine, bar_ids):
    rows = engine.execute(select([foo_table.c.id, foo_table.c.bar_id])
                          .where(foo_table.c.bar_id.in_(bar_ids))).fetchall()
    mapping = defaultdict(list)
    for row in rows:
        mapping[row.bar_id].append(row.id)
    return [mapping[bar_id] for bar_id in bar_ids]


foo_edge = Edge('foo', {
    'id': Field('id', query_foo),
    'name': Field('name', query_foo),
    'count': Field('count', query_foo),
    'bar_id': Field('bar_id', query_foo),

    'bar': Link('bar_id', 'bar', foo_bar_link, False),
})

bar_edge = Edge('bar', {
    'id': Field('id', query_bar),
    'name': Field('name', query_bar),
    'type': Field('type', query_bar),

    'foo_list': Link('id', 'foo', bar_foo_link, True),
})


def query_edge(engine, store, edge, fields, ids):
    mapping = defaultdict(list)
    for field_name in fields:
        field = edge.fields[field_name]
        if isinstance(field, Link):
            field = edge.fields[field.requires]
        mapping[field.func].append(field.name)

    for func, names in mapping.items():
        rows = func(engine, names, ids)
        for row_id, row in zip(ids, rows):
            store.update(edge.name, row_id, zip(names, row))


def query_link(engine, store, edge, link_name, ids):
    link = edge.fields[link_name]
    if link.is_list:
        from_ids = [store.ref(edge.name, i)[link.requires] for i in ids]
        to_ids_list = link.func(engine, from_ids)
        for from_id, to_ids in zip(from_ids, to_ids_list):
            store.update(edge.name, from_id,
                         [(link_name, [store.ref(link.entity, i)
                                       for i in to_ids])])
        return list(chain.from_iterable(to_ids_list))
    else:
        from_ids = [store.ref(edge.name, i)[link.requires] for i in ids]
        to_ids = link.func(engine, from_ids)
        for from_id, to_id in zip(from_ids, to_ids):
            store.update(edge.name, from_id,
                         [(link_name, store.ref(link.entity, to_id))])
        return to_ids


ENV = {
    'foo': foo_edge,
    'bar': bar_edge,
}

executor = ThreadPoolExecutor(2)

futures_set = set()
futures_callbacks = defaultdict(list)


def store_rows(fut_result, store, edge_name, names, ids):
    for row_id, row in zip(ids, fut_result):
        store.update(edge_name, row_id, zip(names, row))


def store_links(fut_result, store, edge, link_name, requirements):
    link = edge.fields[link_name]
    if link.is_list:
        for from_id, to_ids in zip(requirements, fut_result):
            store.update(edge.name, from_id,
                         [(link_name, [store.ref(link.entity, i)
                                       for i in to_ids])])
    else:
        for from_id, to_id in zip(requirements, fut_result):
            store.update(edge.name, from_id,
                         [(link_name, store.ref(link.entity, to_id))])


def process_linked_edge(fut_result, engine, store, link, fields):
    if link.is_list:
        to_ids = list(chain.from_iterable(fut_result))
    else:
        to_ids = fut_result
    process_edge(engine, store, link.entity, fields, to_ids)


def process_link(fut_result, engine, store, edge, link_name, fields, ids):
    link = edge.fields[link_name]
    requirements = [store.ref(edge.name, i)[link.requires] for i in ids]
    fut = executor.submit(link.func, engine, requirements)
    futures_set.add(fut)
    futures_callbacks[fut]\
        .append((store_links, store, edge, link_name, requirements))
    futures_callbacks[fut]\
        .append((process_linked_edge, engine, store, link, fields))


def process_edge(engine, store, edge_name, fields, ids):
    edge = ENV[edge_name]

    field_names = []
    links = []

    for field in fields:
        if isinstance(field, Keyword):
            field_names.append(field)
        elif isinstance(field, Dict):
            for key, value in field.items():
                field_names.append(key)
                # TODO: some links can be queried in parallel with current edge
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
        fut = executor.submit(func, engine, names, ids)
        futures_set.add(fut)
        futures_callbacks[fut]\
            .append((store_rows, store, edge.name, names, ids))
        for name in names:
            name_to_fut[name] = fut

    for edge_name, link_name, fields in links:
        edge = ENV[edge_name]
        link = edge.fields[link_name]
        fut = name_to_fut[link.requires]
        futures_callbacks[fut].append((process_link, engine, store, edge,
                                       link_name, fields, ids))


def wait_processing():
    while futures_set:
        done, _ = wait(futures_set, return_when=FIRST_COMPLETED)
        for fut in done:
            for cb_tuple in futures_callbacks[fut]:
                fn, args = cb_tuple[0], cb_tuple[1:]
                fn(fut.result(), *args)
            futures_set.remove(fut)


class TestSourceSQL(TestCase):

    def setUp(self):
        self.engine = e = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        metadata.create_all(e)

        bar_insert = lambda r: e.execute(bar_table.insert(), r).lastrowid
        self.bar_ids = list(map(bar_insert, [
            {'name': 'bar1', 'type': 1},
            {'name': 'bar2', 'type': 2},
            {'name': 'bar3', 'type': 3},
        ]))

        foo_insert = lambda r: e.execute(foo_table.insert(), r).lastrowid
        list(map(foo_insert, [
            {'name': 'foo1', 'count': 5, 'bar_id': self.bar_ids[0]},
            {'name': 'foo2', 'count': 10, 'bar_id': self.bar_ids[1]},
            {'name': 'foo3', 'count': 15, 'bar_id': self.bar_ids[2]},
        ]))

    def test_m2o(self):
        foo_ids = [3, 2, 1]
        store = Store()

        pattern = read(b'{:foo [:name :count {:bar [:name :type]}]}')
        (edge_name, fields), = pattern.items()

        process_edge(self.engine, store, edge_name, fields, foo_ids)
        wait_processing()

        self.assertEqual(
            [store.ref('foo', i) for i in [3, 2, 1]],
            [
                {'name': 'foo3', 'count': 15, 'bar_id': 3,
                 'bar': {'name': 'bar3', 'type': 3}},
                {'name': 'foo2', 'count': 10, 'bar_id': 2,
                 'bar': {'name': 'bar2', 'type': 2}},
                {'name': 'foo1', 'count': 5, 'bar_id': 1,
                 'bar': {'name': 'bar1', 'type': 1}},
            ]
        )

    def test_o2m(self):
        bar_ids = [3, 2, 1]
        store = Store()

        pattern = read(b'{:bar [:name :type {:foo_list [:name :count]}]}')
        (edge_name, fields), = pattern.items()

        process_edge(self.engine, store, edge_name, fields, bar_ids)
        wait_processing()

        self.assertEqual(
            [store.ref('bar', i) for i in [3, 2, 1]],
            [
                {'id': 3, 'name': 'bar3', 'type': 3, 'foo_list': [
                    {'name': 'foo3', 'count': 15},
                ]},
                {'id': 2, 'name': 'bar2', 'type': 2, 'foo_list': [
                    {'name': 'foo2', 'count': 10},
                ]},
                {'id': 1, 'name': 'bar1', 'type': 1, 'foo_list': [
                    {'name': 'foo1', 'count': 5},
                ]},
            ],
        )
