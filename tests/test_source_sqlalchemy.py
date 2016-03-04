from __future__ import unicode_literals

from itertools import chain
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.types import IntegerType, StringType
from hiku.graph import Graph, Edge, Link
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor
from hiku.sources.sqlalchemy import db_fields, db_link

from .base import TestCase


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
    return [6, 5, 4]


def not_found_one():
    return -1


def not_found_list():
    return [6, -1, 4]


def direct_link(ids):
    return ids


GRAPH = Graph([
    Edge(foo_table.name, chain(
        db_fields(session, foo_table, [
            'id',
            'name',
            'count',
            'bar_id',
        ]),
        [
            Link('bar', 'bar_id', 'bar', direct_link, to_list=False),
        ],
    )),
    Edge(bar_table.name, chain(
        db_fields(session, bar_table, [
            'id',
            'name',
            'type',
        ]),
        [
            db_link(session, 'foo-s', 'id',
                    foo_table.c.bar_id, foo_table.c.id, to_list=True),
        ],
    )),
    Link('foo-list', None, foo_table.name, foo_list, to_list=True),
    Link('bar-list', None, bar_table.name, bar_list, to_list=True),
    Link('not-found-one', None, bar_table.name, not_found_one, to_list=False),
    Link('not-found-list', None, bar_table.name, not_found_list, to_list=True),
])

thread_pool = ThreadPoolExecutor(2)


class TestSourceSQL(TestCase):

    def setUp(self):
        sa_engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        metadata.create_all(sa_engine)
        session.configure(bind=sa_engine)

        for r in [
            {'id': 4, 'name': 'bar1', 'type': 1},
            {'id': 5, 'name': 'bar2', 'type': 2},
            {'id': 6, 'name': 'bar3', 'type': 3},
        ]:
            sa_engine.execute(bar_table.insert(), r)

        for r in [
            {'name': 'foo1', 'count': 5, 'bar_id': 6},
            {'name': 'foo2', 'count': 10, 'bar_id': 5},
            {'name': 'foo3', 'count': 15, 'bar_id': 4},
            {'name': 'foo4', 'count': 20, 'bar_id': 6},
            {'name': 'foo5', 'count': 25, 'bar_id': 5},
            {'name': 'foo6', 'count': 30, 'bar_id': 4},
        ]:
            sa_engine.execute(foo_table.insert(), r)

        self.engine = Engine(ThreadsExecutor(thread_pool))

    def tearDown(self):
        session.remove()

    def testTypes(self):
        self.assertIsInstance(GRAPH.fields[foo_table.name].fields['id'].type,
                              IntegerType)
        self.assertIsInstance(GRAPH.fields[foo_table.name].fields['name'].type,
                              StringType)

    def assertExecute(self, src, value):
        result = self.engine.execute(GRAPH, read(src))
        self.assertResult(result, value)

    def testSameTable(self):
        with self.assertRaisesRegexp(ValueError, 'should belong'):
            db_link(session, 'name', 'requires',
                    foo_table.c.id, bar_table.c.id, to_list=True)

    def testSameColumn(self):
        with self.assertRaisesRegexp(ValueError, 'same column'):
            db_link(session, 'name', 'requires',
                    foo_table.c.id, foo_table.c.id, to_list=True)

    def testMissingColumn(self):
        with self.assertRaisesRegexp(ValueError, 'does not have a column'):
            db_fields(session, foo_table, ['unknown'])

    def testManyToOne(self):
        self.assertExecute(
            '[{:foo-list [:name :count {:bar [:name :type]}]}]',
            {'foo-list': [
                {'name': 'foo3', 'count': 15, 'bar_id': 4,
                 'bar': {'name': 'bar1', 'type': 1}},
                {'name': 'foo2', 'count': 10, 'bar_id': 5,
                 'bar': {'name': 'bar2', 'type': 2}},
                {'name': 'foo1', 'count': 5, 'bar_id': 6,
                 'bar': {'name': 'bar3', 'type': 3}},
            ]}
        )

    def testOneToMany(self):
        self.assertExecute(
            '[{:bar-list [:name :type {:foo-s [:name :count]}]}]',
            {'bar-list': [
                {'id': 6, 'name': 'bar3', 'type': 3, 'foo-s': [
                    {'name': 'foo1', 'count': 5},
                    {'name': 'foo4', 'count': 20},
                ]},
                {'id': 5, 'name': 'bar2', 'type': 2, 'foo-s': [
                    {'name': 'foo2', 'count': 10},
                    {'name': 'foo5', 'count': 25},
                ]},
                {'id': 4, 'name': 'bar1', 'type': 1, 'foo-s': [
                    {'name': 'foo3', 'count': 15},
                    {'name': 'foo6', 'count': 30},
                ]},
            ]},
        )

    def testNotFound(self):
        self.assertExecute(
            '[{:not-found-one [:name :type]}'
            ' {:not-found-list [:name :type]}]',
            {
                'not-found-one': {'name': None, 'type': None},
                'not-found-list': [
                    {'name': 'bar3', 'type': 3},
                    {'name': None, 'type': None},
                    {'name': 'bar1', 'type': 1},
                ],
            },
        )
