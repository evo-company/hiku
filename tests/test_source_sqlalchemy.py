from __future__ import unicode_literals

from abc import ABCMeta, abstractproperty, abstractmethod
from concurrent.futures import ThreadPoolExecutor

import pytest

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.types import IntegerMeta, StringMeta, TypeRef, Sequence, Optional
from hiku.graph import Graph, Edge, Link, Root
from hiku.utils import cached_property
from hiku.compat import with_metaclass
from hiku.engine import Engine
from hiku.sources import sqlalchemy as sa
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor

from .base import check_result


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

thread_pool = ThreadPoolExecutor(2)


class AbstractQueries(with_metaclass(ABCMeta)):

    @abstractproperty
    def foo_query(self):
        pass

    @abstractproperty
    def bar_query(self):
        pass

    @abstractproperty
    def to_foo_query(self):
        pass

    @abstractproperty
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

        to_foo_query = _sm.LinkQuery(Sequence[TypeRef['foo']], ctx_var,
                                     from_column=foo_table.c.bar_id,
                                     to_column=foo_table.c.id)

        to_bar_query = _sm.LinkQuery(Optional[TypeRef['bar']], ctx_var,
                                     from_column=bar_table.c.id,
                                     to_column=bar_table.c.id)

    return Queries()


def get_graph(source_module, queries):
    _sm = source_module
    _q = queries

    return Graph([
        Edge(foo_table.name, [
            _sm.Field('id', _q.foo_query),
            _sm.Field('name', _q.foo_query),
            _sm.Field('count', _q.foo_query),
            _sm.Field('bar_id', _q.foo_query),
            _sm.Link('bar', _q.to_bar_query, requires='bar_id'),
        ]),
        Edge(bar_table.name, [
            _sm.Field('id', _q.bar_query),
            _sm.Field('name', _q.bar_query),
            _sm.Field('type', _q.bar_query),
            _sm.Link('foo-s', _q.to_foo_query, requires='id'),
        ]),
        Root([
            Link('foo-list', Sequence[TypeRef['foo']],
                 _q.foo_list, requires=None),
            Link('bar-list', Sequence[TypeRef['bar']],
                 _q.bar_list, requires=None),
            Link('not-found-one', TypeRef['bar'],
                 _q.not_found_one, requires=None),
            Link('not-found-list', Sequence[TypeRef['bar']],
                 _q.not_found_list, requires=None),
        ]),
    ])


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

    @abstractproperty
    def queries(self):
        pass

    @abstractmethod
    def check(self, src, value):
        pass

    @cached_property
    def graph(self):
        return get_graph(sa, self.queries)

    def test_types(self):
        assert isinstance(
            self.graph.edges_map[foo_table.name].fields_map['id'].type,
            IntegerMeta,
        )
        assert isinstance(
            self.graph.edges_map[foo_table.name].fields_map['name'].type,
            StringMeta,
        )

    def test_same_table(self):
        with pytest.raises(ValueError) as e:
            sa.LinkQuery(Sequence[TypeRef['bar']], SA_ENGINE,
                         from_column=foo_table.c.id,
                         to_column=bar_table.c.id)
        e.match('should belong')

    def test_missing_column(self):
        with pytest.raises(ValueError) as e:
            sa.Field('unknown', self.queries.foo_query)
        e.match('does not have a column')

    def test_many_to_one(self):
        self.check(
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

    def test_one_to_many(self):
        self.check(
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

    def test_not_found(self):
        self.check(
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


class TestSourceSQLAlchemy(SourceSQLAlchemyTestBase):

    @cached_property
    def queries(self):
        return get_queries(sa, SA_ENGINE, SyncQueries)

    def check(self, src, value):
        sa_engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
        setup_db(sa_engine)

        engine = Engine(ThreadsExecutor(thread_pool))
        result = engine.execute(self.graph, read(src), {SA_ENGINE: sa_engine})
        check_result(result, value)
