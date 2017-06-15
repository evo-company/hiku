from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor

import pytest

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

import hiku.sources.sqlalchemy

from hiku.types import IntegerMeta, StringMeta, TypeRef, Sequence, Optional
from hiku.graph import Graph, Node, Field, Link, Root
from hiku.utils import cached_property
from hiku.compat import with_metaclass
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor
from hiku.sources.sqlalchemy import LinkQuery

from .base import check_result


SA_ENGINE_KEY = 'sa-engine'

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

thread_pool = ThreadPoolExecutor(2)


class AbstractQueries(with_metaclass(ABCMeta)):

    @property
    @abstractmethod
    def foo_query(self):
        pass

    @property
    @abstractmethod
    def bar_query(self):
        pass

    @property
    @abstractmethod
    def to_foo_query(self):
        pass

    @property
    @abstractmethod
    def to_bar_query(self):
        pass

    @abstractmethod
    def foo_list(self):
        pass

    @abstractmethod
    def bar_list(self):
        pass

    @abstractmethod
    def not_found_one(self):
        pass

    @abstractmethod
    def not_found_list(self):
        pass


class SyncQueries(AbstractQueries):

    def foo_list(self):
        return [3, 2, 1]

    def bar_list(self):
        return [6, 5, 4]

    def not_found_one(self):
        return -1

    def not_found_list(self):
        return [6, -1, 4]


def get_queries(source_module, ctx_var, base_cls):
    _sm = source_module

    class Queries(base_cls):
        foo_query = _sm.FieldsQuery(ctx_var, foo_table)

        bar_query = _sm.FieldsQuery(ctx_var, bar_table)

        to_foo_query = _sm.LinkQuery(
            ctx_var,
            from_column=foo_table.c.bar_id,
            to_column=foo_table.c.id,
        )

        to_bar_query = _sm.LinkQuery(
            ctx_var,
            from_column=bar_table.c.id,
            to_column=bar_table.c.id,
        )

    return Queries()


def get_graph(queries):
    _q = queries

    graph = Graph([
        Node(foo_table.name, [
            Field('id', None, _q.foo_query),
            Field('name', None, _q.foo_query),
            Field('count', None, _q.foo_query),
            Field('bar_id', None, _q.foo_query),
            Link('bar', Optional[TypeRef['bar']], _q.to_bar_query,
                 requires='bar_id'),
        ]),
        Node(bar_table.name, [
            Field('id', None, _q.bar_query),
            Field('name', None, _q.bar_query),
            Field('type', None, _q.bar_query),
            Link('foo_s', Sequence[TypeRef['foo']], _q.to_foo_query,
                 requires='id'),
        ]),
        Root([
            Link('foo_list', Sequence[TypeRef['foo']],
                 _q.foo_list, requires=None),
            Link('bar_list', Sequence[TypeRef['bar']],
                 _q.bar_list, requires=None),
            Link('not_found_one', TypeRef['bar'],
                 _q.not_found_one, requires=None),
            Link('not_found_list', Sequence[TypeRef['bar']],
                 _q.not_found_list, requires=None),
        ]),
    ])
    return graph


def setup_db(db_engine):
    metadata.create_all(db_engine)
    for r in [
        {'id': 4, 'name': 'bar1', 'type': 1},
        {'id': 5, 'name': 'bar2', 'type': 2},
        {'id': 6, 'name': 'bar3', 'type': 3},
    ]:
        db_engine.execute(bar_table.insert(), r)
    for r in [
        {'name': 'foo1', 'count': 5, 'bar_id': None},
        {'name': 'foo2', 'count': 10, 'bar_id': 5},
        {'name': 'foo3', 'count': 15, 'bar_id': 4},
        {'name': 'foo4', 'count': 20, 'bar_id': 6},
        {'name': 'foo5', 'count': 25, 'bar_id': 5},
        {'name': 'foo6', 'count': 30, 'bar_id': 4},
    ]:
        db_engine.execute(foo_table.insert(), r)


class SourceSQLAlchemyTestBase(with_metaclass(ABCMeta, object)):

    @property
    @abstractmethod
    def queries(self):
        pass

    @abstractmethod
    def check(self, src, value):
        pass

    @cached_property
    def graph(self):
        return get_graph(self.queries)

    def test_types(self):
        assert isinstance(
            self.graph.nodes_map[foo_table.name].fields_map['id'].type,
            IntegerMeta,
        )
        assert isinstance(
            self.graph.nodes_map[foo_table.name].fields_map['name'].type,
            StringMeta,
        )

    def test_same_table(self):
        with pytest.raises(ValueError) as e:
            LinkQuery(SA_ENGINE_KEY, from_column=foo_table.c.id,
                      to_column=bar_table.c.id)
        e.match('should belong')

    def test_many_to_one(self):
        self.check(
            '[{:foo_list [:name :count {:bar [:name :type]}]}]',
            {'foo_list': [
                {'name': 'foo3', 'count': 15, 'bar_id': 4,
                 'bar': {'name': 'bar1', 'type': 1}},
                {'name': 'foo2', 'count': 10, 'bar_id': 5,
                 'bar': {'name': 'bar2', 'type': 2}},
                {'name': 'foo1', 'count': 5, 'bar_id': None,
                 'bar': None},
            ]}
        )

    def test_one_to_many(self):
        self.check(
            '[{:bar_list [:name :type {:foo_s [:name :count]}]}]',
            {'bar_list': [
                {'id': 6, 'name': 'bar3', 'type': 3, 'foo_s': [
                    {'name': 'foo4', 'count': 20},
                ]},
                {'id': 5, 'name': 'bar2', 'type': 2, 'foo_s': [
                    {'name': 'foo2', 'count': 10},
                    {'name': 'foo5', 'count': 25},
                ]},
                {'id': 4, 'name': 'bar1', 'type': 1, 'foo_s': [
                    {'name': 'foo3', 'count': 15},
                    {'name': 'foo6', 'count': 30},
                ]},
            ]},
        )

    def test_not_found(self):
        self.check(
            '[{:not_found_one [:name :type]}'
            ' {:not_found_list [:name :type]}]',
            {
                'not_found_one': {'name': None, 'type': None},
                'not_found_list': [
                    {'name': 'bar3', 'type': 3},
                    {'name': None, 'type': None},
                    {'name': 'bar1', 'type': 1},
                ],
            },
        )


class TestSourceSQLAlchemy(SourceSQLAlchemyTestBase):

    @cached_property
    def queries(self):
        return get_queries(hiku.sources.sqlalchemy, SA_ENGINE_KEY, SyncQueries)

    def check(self, src, value):
        sa_engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        setup_db(sa_engine)

        engine = Engine(ThreadsExecutor(thread_pool))
        result = engine.execute(self.graph, read(src),
                                {SA_ENGINE_KEY: sa_engine})
        check_result(result, value)
