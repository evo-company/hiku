from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

import pytest

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey

from hiku.types import IntegerMeta, StringMeta, TypeRef, Sequence, Optional
from hiku.graph import Graph, Node, Field, Link, Root
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.threads import ThreadsExecutor
from hiku.sources.sqlalchemy import LinkQuery, FieldsQuery

from .base import check_result


def asyncify(fn):
    async def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper


SA_ENGINE_KEY = "sa-engine"

metadata = MetaData()

thread_pool = ThreadPoolExecutor(2)

foo_table = Table(
    "foo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Unicode),
    Column("count", Integer),
    Column("bar_id", ForeignKey("bar.id")),
)

bar_table = Table(
    "bar",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Unicode),
    Column("type", Integer),
)


def setup_db(db_engine):
    metadata.create_all(db_engine)
    for r in [
        {"id": 0, "name": "bar0", "type": 4},
        {"id": 4, "name": "bar1", "type": 1},
        {"id": 5, "name": "bar2", "type": 2},
        {"id": 6, "name": "bar3", "type": 3},
    ]:
        db_engine.execute(bar_table.insert(), r)
    for r in [
        {"name": "foo1", "count": 5, "bar_id": None},
        {"name": "foo2", "count": 10, "bar_id": 5},
        {"name": "foo3", "count": 15, "bar_id": 4},
        {"name": "foo4", "count": 20, "bar_id": 6},
        {"name": "foo5", "count": 25, "bar_id": 5},
        {"name": "foo6", "count": 30, "bar_id": 4},
        {"name": "foo7", "count": 35, "bar_id": 0},
    ]:
        db_engine.execute(foo_table.insert(), r)


def graph_factory(
    *, async_=False, fields_query_cls=FieldsQuery, link_query_cls=LinkQuery
):
    def foo_list():
        return [3, 2, 1]

    def bar_list():
        return [6, 5, 4]

    def not_found_one():
        return -1

    def not_found_list():
        return [6, -1, 4]

    def falsy_one():
        """foo:7 refer to bar:0"""
        return 0

    if async_:
        foo_list = asyncify(foo_list)
        bar_list = asyncify(bar_list)
        not_found_one = asyncify(not_found_one)
        not_found_list = asyncify(not_found_list)
        falsy_one = asyncify(falsy_one)

    foo_query = fields_query_cls(SA_ENGINE_KEY, foo_table)

    bar_query = fields_query_cls(SA_ENGINE_KEY, bar_table)

    to_foo_query = link_query_cls(
        SA_ENGINE_KEY,
        from_column=foo_table.c.bar_id,
        to_column=foo_table.c.id,
    )

    to_bar_query = link_query_cls(
        SA_ENGINE_KEY,
        from_column=bar_table.c.id,
        to_column=bar_table.c.id,
    )

    graph = Graph(
        [
            Node(
                foo_table.name,
                [
                    Field("id", None, foo_query),
                    Field("name", None, foo_query),
                    Field("count", None, foo_query),
                    Field("bar_id", None, foo_query),
                    Link(
                        "bar",
                        Optional[TypeRef["bar"]],
                        to_bar_query,
                        requires="bar_id",
                    ),
                ],
            ),
            Node(
                bar_table.name,
                [
                    Field("id", None, bar_query),
                    Field("name", None, bar_query),
                    Field("type", None, bar_query),
                    Link(
                        "foo_s",
                        Sequence[TypeRef["foo"]],
                        to_foo_query,
                        requires="id",
                    ),
                ],
            ),
            Root(
                [
                    Link(
                        "foo_list",
                        Sequence[TypeRef["foo"]],
                        foo_list,
                        requires=None,
                    ),
                    Link(
                        "bar_list",
                        Sequence[TypeRef["bar"]],
                        bar_list,
                        requires=None,
                    ),
                    Link(
                        "not_found_one",
                        TypeRef["bar"],
                        not_found_one,
                        requires=None,
                    ),
                    Link(
                        "not_found_list",
                        Sequence[TypeRef["bar"]],
                        not_found_list,
                        requires=None,
                    ),
                    Link("falsy_one", TypeRef["bar"], falsy_one, requires=None),
                ]
            ),
        ]
    )
    return graph


@pytest.fixture(name="graph")
def graph_fixture(request):
    graph = graph_factory()
    if request.instance:
        # for class-based tests
        request.instance.graph = graph
    return graph


def test_same_table():
    with pytest.raises(ValueError) as e:
        LinkQuery(
            SA_ENGINE_KEY, from_column=foo_table.c.id, to_column=bar_table.c.id
        )
    e.match("should belong")


def test_types(graph):
    assert isinstance(
        graph.nodes_map[foo_table.name].fields_map["id"].type,
        IntegerMeta,
    )
    assert isinstance(
        graph.nodes_map[foo_table.name].fields_map["name"].type,
        StringMeta,
    )


class SourceSQLAlchemyTestBase(ABC):
    @abstractmethod
    def check(self, src, value):
        pass

    def test_many_to_one(self):
        self.check(
            "[{:foo_list [:name :count :bar_id {:bar [:name :type]}]}]",
            {
                "foo_list": [
                    {
                        "name": "foo3",
                        "count": 15,
                        "bar_id": 4,
                        "bar": {"name": "bar1", "type": 1},
                    },
                    {
                        "name": "foo2",
                        "count": 10,
                        "bar_id": 5,
                        "bar": {"name": "bar2", "type": 2},
                    },
                    {"name": "foo1", "count": 5, "bar_id": None, "bar": None},
                ]
            },
        )

    def test_one_to_many(self):
        self.check(
            "[{:bar_list [:id :name :type {:foo_s [:name :count]}]}]",
            {
                "bar_list": [
                    {
                        "id": 6,
                        "name": "bar3",
                        "type": 3,
                        "foo_s": [
                            {"name": "foo4", "count": 20},
                        ],
                    },
                    {
                        "id": 5,
                        "name": "bar2",
                        "type": 2,
                        "foo_s": [
                            {"name": "foo2", "count": 10},
                            {"name": "foo5", "count": 25},
                        ],
                    },
                    {
                        "id": 4,
                        "name": "bar1",
                        "type": 1,
                        "foo_s": [
                            {"name": "foo3", "count": 15},
                            {"name": "foo6", "count": 30},
                        ],
                    },
                ]
            },
        )

    def test_not_found(self):
        self.check(
            "[{:not_found_one [:name :type]}"
            " {:not_found_list [:name :type]}]",
            {
                "not_found_one": {"name": None, "type": None},
                "not_found_list": [
                    {"name": "bar3", "type": 3},
                    {"name": None, "type": None},
                    {"name": "bar1", "type": 1},
                ],
            },
        )

    def test_falsy_one(self):
        self.check(
            "[{:falsy_one [:name :type {:foo_s [:name :count]}]}]",
            {
                "falsy_one": {
                    "name": "bar0",
                    "type": 4,
                    "foo_s": [
                        {"name": "foo7", "count": 35},
                    ],
                }
            },
        )


@pytest.mark.usefixtures("graph")
class TestSourceSQLAlchemy(SourceSQLAlchemyTestBase):
    def check(self, src, value):
        sa_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        setup_db(sa_engine)

        engine = Engine(ThreadsExecutor(thread_pool))
        result = engine.execute(
            self.graph, read(src), {SA_ENGINE_KEY: sa_engine}
        )
        check_result(result, value)
