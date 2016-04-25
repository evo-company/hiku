from __future__ import unicode_literals

from itertools import chain
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.types import IntegerType, StringType
from hiku.graph import Graph, Edge, link
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor
from hiku.sources.sqlalchemy import fields as sa_fields, link as sa_link

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


@link.many('foo', requires=False)
def foo_list():
    return [3, 2, 1]


@link.many('bar', requires=False)
def bar_list():
    return [6, 5, 4]


@link.one('bar', requires=False)
def not_found_one():
    return -1


@link.many('bar', requires=False)
def not_found_list():
    return [6, -1, 4]


@link.one('bar', requires=True)
def direct_link(ids):
    return ids


@sa_link.many('foo', session, from_=foo_table.c.bar_id, to=foo_table.c.id)
def to_foo(expr):
    return expr


@sa_link.one('bar', session, from_=bar_table.c.id, to=bar_table.c.id)
def to_bar(expr):
    return expr


GRAPH = Graph([
    Edge(foo_table.name, chain(
        sa_fields(session, foo_table, [
            'id',
            'name',
            'count',
            'bar_id',
        ]),
        [
            to_bar('bar', requires='bar_id'),
        ],
    )),
    Edge(bar_table.name, chain(
        sa_fields(session, bar_table, [
            'id',
            'name',
            'type',
        ]),
        [
            to_foo('foo-s', requires='id'),
        ],
    )),
    foo_list('foo-list'),
    bar_list('bar-list'),
    not_found_one('not-found-one'),
    not_found_list('not-found-list'),
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
            sa_link.many('name', session,
                         from_=foo_table.c.id, to=bar_table.c.id)

    def testMissingColumn(self):
        with self.assertRaisesRegexp(ValueError, 'does not have a column'):
            sa_fields(session, foo_table, ['unknown'])

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
