from __future__ import unicode_literals

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.types import IntegerMeta, StringMeta
from hiku.graph import Graph, Edge, Link, Root, Many, One, Maybe
from hiku.engine import Engine
from hiku.sources import sqlalchemy as sa
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import TestCase


SA_ENGINE = 'sa-engine'

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


def foo_list():
    return [3, 2, 1]


def bar_list():
    return [6, 5, 4]


def not_found_one():
    return -1


def not_found_list():
    return [6, -1, 4]


foo_query = sa.FieldsQuery(SA_ENGINE, foo_table)

bar_query = sa.FieldsQuery(SA_ENGINE, bar_table)


to_foo_query = sa.LinkQuery(Many, SA_ENGINE, edge='foo',
                            from_column=foo_table.c.bar_id,
                            to_column=foo_table.c.id)

to_bar_query = sa.LinkQuery(Maybe, SA_ENGINE, edge='bar',
                            from_column=bar_table.c.id,
                            to_column=bar_table.c.id)


GRAPH = Graph([
    Edge(foo_table.name, [
        sa.Field('id', foo_query),
        sa.Field('name', foo_query),
        sa.Field('count', foo_query),
        sa.Field('bar_id', foo_query),
        sa.Link('bar', to_bar_query, requires='bar_id'),
    ]),
    Edge(bar_table.name, [
        sa.Field('id', bar_query),
        sa.Field('name', bar_query),
        sa.Field('type', bar_query),
        sa.Link('foo-s', to_foo_query, requires='id'),
    ]),
    Root([
        Link('foo-list', Many, foo_list, edge='foo', requires=None),
        Link('bar-list', Many, bar_list, edge='bar', requires=None),
        Link('not-found-one', One, not_found_one, edge='bar', requires=None),
        Link('not-found-list', Many, not_found_list, edge='bar', requires=None),
    ]),
])

thread_pool = ThreadPoolExecutor(2)


class TestSourceSQL(TestCase):

    def setUp(self):
        self.sa_engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        metadata.create_all(self.sa_engine)

        for r in [
            {'id': 4, 'name': 'bar1', 'type': 1},
            {'id': 5, 'name': 'bar2', 'type': 2},
            {'id': 6, 'name': 'bar3', 'type': 3},
        ]:
            self.sa_engine.execute(bar_table.insert(), r)

        for r in [
            {'name': 'foo1', 'count': 5, 'bar_id': None},
            {'name': 'foo2', 'count': 10, 'bar_id': 5},
            {'name': 'foo3', 'count': 15, 'bar_id': 4},
            {'name': 'foo4', 'count': 20, 'bar_id': 6},
            {'name': 'foo5', 'count': 25, 'bar_id': 5},
            {'name': 'foo6', 'count': 30, 'bar_id': 4},
        ]:
            self.sa_engine.execute(foo_table.insert(), r)

        self.engine = Engine(ThreadsExecutor(thread_pool))

    def testTypes(self):
        self.assertIsInstance(
            GRAPH.edges_map[foo_table.name].fields_map['id'].type,
            IntegerMeta,
        )
        self.assertIsInstance(
            GRAPH.edges_map[foo_table.name].fields_map['name'].type,
            StringMeta,
        )

    def assertExecute(self, src, value):
        result = self.engine.execute(GRAPH, read(src),
                                     {SA_ENGINE: self.sa_engine})
        self.assertResult(result, value)

    def testSameTable(self):
        with self.assertRaisesRegexp(ValueError, 'should belong'):
            sa.LinkQuery(Many, SA_ENGINE, edge='bar',
                         from_column=foo_table.c.id,
                         to_column=bar_table.c.id)

    def testMissingColumn(self):
        with self.assertRaisesRegexp(ValueError, 'does not have a column'):
            sa.Field('unknown', foo_query)

    def testManyToOne(self):
        self.assertExecute(
            '[{:foo-list [:name :count {:bar [:name :type]}]}]',
            {'foo-list': [
                {'name': 'foo3', 'count': 15, 'bar_id': 4,
                 'bar': {'name': 'bar1', 'type': 1}},
                {'name': 'foo2', 'count': 10, 'bar_id': 5,
                 'bar': {'name': 'bar2', 'type': 2}},
                {'name': 'foo1', 'count': 5, 'bar_id': None,
                 'bar': None},
            ]}
        )

    def testOneToMany(self):
        self.assertExecute(
            '[{:bar-list [:name :type {:foo-s [:name :count]}]}]',
            {'bar-list': [
                {'id': 6, 'name': 'bar3', 'type': 3, 'foo-s': [
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
