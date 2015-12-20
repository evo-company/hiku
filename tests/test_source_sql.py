from __future__ import unicode_literals

from unittest import TestCase
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, select
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.graph import Edge, Link
from hiku.engine import Engine
from hiku.compat import PY3
from hiku.sources.sql import db_fields
from hiku.executors.thread import ThreadExecutor

if not PY3:
    import warnings
    from sqlalchemy.exc import SAWarning
    warnings.filterwarnings('ignore', '', SAWarning, '', 0)


metadata = MetaData()
session = scoped_session(sessionmaker())


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


def foo_bar_link(bar_ids):
    return bar_ids


def bar_foo_link(bar_ids):
    rows = (
        session.execute(select([foo_table.c.id, foo_table.c.bar_id])
                        .where(foo_table.c.bar_id.in_(bar_ids)))
        .fetchall()
    )
    mapping = defaultdict(list)
    for row in rows:
        mapping[row.bar_id].append(row.id)
    return [mapping[bar_id] for bar_id in bar_ids]


def foo_list():
    return [3, 2, 1]


def bar_list():
    return [3, 2, 1]


ENV = [
    Edge('foo',
         db_fields(session, foo_table, [
            'id',
            'name',
            'count',
            'bar_id',
         ]) + [
             Link('bar', 'bar_id', 'bar', foo_bar_link),
         ]),
    Edge('bar',
         db_fields(session, bar_table, [
             'id',
             'name',
             'type',
         ]) + [
             Link('foo-s', 'id', 'foo', bar_foo_link, to_list=True),
         ]),
    Link('foo-list', None, 'foo', foo_list, to_list=True),
    Link('bar-list', None, 'bar', bar_list, to_list=True),
]

thread_pool = ThreadPoolExecutor(2)


class TestSourceSQL(TestCase):

    def setUp(self):
        engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        metadata.create_all(engine)
        session.configure(bind=engine)

        bar_insert = lambda r: engine.execute(bar_table.insert(), r).lastrowid
        self.bar_ids = list(map(bar_insert, [
            {'name': 'bar1', 'type': 1},
            {'name': 'bar2', 'type': 2},
            {'name': 'bar3', 'type': 3},
        ]))

        foo_insert = lambda r: engine.execute(foo_table.insert(), r).lastrowid
        list(map(foo_insert, [
            {'name': 'foo1', 'count': 5, 'bar_id': self.bar_ids[0]},
            {'name': 'foo2', 'count': 10, 'bar_id': self.bar_ids[1]},
            {'name': 'foo3', 'count': 15, 'bar_id': self.bar_ids[2]},
        ]))

    def tearDown(self):
        session.remove()

    def test_m2o(self):
        engine = Engine(ENV, ThreadExecutor(thread_pool))
        result = engine.execute(
            '[{:foo-list [:name :count {:bar [:name :type]}]}]',
        )
        self.assertEqual(
            result['foo-list'],
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
        engine = Engine(ENV, ThreadExecutor(thread_pool))
        result = engine.execute(
            '[{:bar-list [:name :type {:foo-s [:name :count]}]}]',
        )
        self.assertEqual(
            result['bar-list'],
            [
                {'id': 3, 'name': 'bar3', 'type': 3, 'foo-s': [
                    {'name': 'foo3', 'count': 15},
                ]},
                {'id': 2, 'name': 'bar2', 'type': 2, 'foo-s': [
                    {'name': 'foo2', 'count': 10},
                ]},
                {'id': 1, 'name': 'bar1', 'type': 1, 'foo-s': [
                    {'name': 'foo1', 'count': 5},
                ]},
            ],
        )
