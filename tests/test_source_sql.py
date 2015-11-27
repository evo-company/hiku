from unittest import TestCase
from itertools import chain
from collections import defaultdict

from sqlalchemy import create_engine, select
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.store import Store


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
    rows = engine.execute(select(columns + [p_key])
                          .where(p_key.in_(idents))).fetchall()
    rows_map = {row[p_key]: row for row in rows}
    return [rows_map.get(ident) for ident in idents]


def query_foo(engine, attrs, idents):
    return _query(engine, foo_table, attrs, idents)


def query_bar(engine, attrs, idents):
    return _query(engine, bar_table, attrs, idents)


def foo_bar_link(engine, foo_rows):
    # needs bar_id in parent query
    return [r.bar_id for r in foo_rows]


def bar_foo_link(engine, bar_rows):
    bar_ids = [r.id for r in bar_rows]
    rows = engine.execute(select([foo_table.c.id, foo_table.c.bar_id])
                          .where(foo_table.c.bar_id.in_(bar_ids))).fetchall()
    mapping = defaultdict(list)
    for row in rows:
        mapping[row.bar_id].append(row.id)
    return [mapping[bar_id] for bar_id in bar_ids]


class TestSourceSQL(TestCase):

    def setUp(self):
        self.engine = e = create_engine('sqlite://')
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
        store = Store()

        foo_rows = query_foo(self.engine, ['name', 'count', 'bar_id'],
                             [3, 2, 1])
        for row in foo_rows:
            store.update(
                'foo',
                row.id,
                zip(['name', 'count', 'bar'],
                    [row.name, row.count, store.ref('bar', row.bar_id)]),
            )

        bar_ids = foo_bar_link(self.engine, foo_rows)
        bar_rows = query_bar(self.engine, ['name', 'type'], bar_ids)
        for row in bar_rows:
            store.update('bar',
                         row.id,
                         zip(['name', 'type'], [row.name, row.type]))

        self.assertEqual(
            [store.ref('foo', i) for i in [3, 2, 1]],
            [
                {'name': 'foo3', 'count': 15,
                 'bar': {'name': 'bar3', 'type': 3}},
                {'name': 'foo2', 'count': 10,
                 'bar': {'name': 'bar2', 'type': 2}},
                {'name': 'foo1', 'count': 5,
                 'bar': {'name': 'bar1', 'type': 1}},
            ]
        )

    def test_o2m(self):
        store = Store()

        bar_rows = query_bar(self.engine, ['id', 'name', 'type'],
                             [3, 2, 1])
        for row in bar_rows:
            store.update('bar',
                         row.id,
                         zip(['name', 'type'], [row.name, row.type]))

        foo_ids_list = bar_foo_link(self.engine, bar_rows)
        for bar_row, foo_ids in zip(bar_rows, foo_ids_list):
            store.update('bar', bar_row.id,
                         [('foo_list', [store.ref('foo', i) for i in foo_ids])])

        foo_rows = query_foo(self.engine, ['name', 'count'],
                             list(chain.from_iterable(foo_ids_list)))
        for row in foo_rows:
            store.update('foo',
                         row.id,
                         zip(['name', 'count'], [row.name, row.count]))

        self.assertEqual(
            [store.ref('bar', i) for i in [3, 2, 1]],
            [
                {'name': 'bar3', 'type': 3, 'foo_list': [
                    {'name': 'foo3', 'count': 15},
                ]},
                {'name': 'bar2', 'type': 2, 'foo_list': [
                    {'name': 'foo2', 'count': 10},
                ]},
                {'name': 'bar1', 'type': 1, 'foo_list': [
                    {'name': 'foo1', 'count': 5},
                ]},
            ],
        )
