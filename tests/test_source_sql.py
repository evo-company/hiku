from __future__ import unicode_literals

from unittest import TestCase
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.graph import Edge, Link
from hiku.engine import Engine
from hiku.sources.sql import db_fields, db_link
from hiku.readers.simple import read
from hiku.executors.thread import ThreadExecutor


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


def foo_list():
    return [3, 2, 1]


def bar_list():
    return [3, 2, 1]


ENV = Edge(None, [
    Edge(foo_table.name,
         db_fields(session, foo_table, [
            'id',
            'name',
            'count',
            'bar_id',
         ]) + [
             db_link(session, 'bar',
                     foo_table.c.bar_id, bar_table.c.id, False),
         ]),
    Edge(bar_table.name,
         db_fields(session, bar_table, [
             'id',
             'name',
             'type',
         ]) + [
             db_link(session, 'foo-s',
                     bar_table.c.id, foo_table.c.bar_id, True),
         ]),
    Link('foo-list', None, foo_table.name, foo_list, to_list=True),
    Link('bar-list', None, bar_table.name, bar_list, to_list=True),
])

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
        engine = Engine(ThreadExecutor(thread_pool))
        result = engine.execute(
            ENV,
            read('[{:foo-list [:name :count {:bar [:name :type]}]}]'),
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
        engine = Engine(ThreadExecutor(thread_pool))
        result = engine.execute(
            ENV,
            read('[{:bar-list [:name :type {:foo-s [:name :count]}]}]'),
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
