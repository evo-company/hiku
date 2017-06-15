import uuid

import pytest
import asyncio
import aiopg.sa
import sqlalchemy
import psycopg2.extensions

from pytest_asyncio.plugin import ForbiddenEventLoopPolicy

import hiku.sources.aiopg

from hiku.utils import cached_property
from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.asyncio import AsyncIOExecutor

from tests.base import check_result
from tests.test_source_sqlalchemy import setup_db, get_queries
from tests.test_source_sqlalchemy import SyncQueries, AbstractQueries
from tests.test_source_sqlalchemy import SourceSQLAlchemyTestBase


SA_ENGINE_KEY = 'sa-engine'


class AsyncQueries(AbstractQueries):

    async def foo_list(self):
        return SyncQueries.foo_list.__call__(self)

    async def bar_list(self):
        return SyncQueries.bar_list.__call__(self)

    async def not_found_one(self):
        return SyncQueries.not_found_one.__call__(self)

    async def not_found_list(self):
        return SyncQueries.not_found_list.__call__(self)


@pytest.fixture(scope='session')
def _db_dsn(request):
    name = 'test_{}'.format(uuid.uuid4().hex)
    pg_dsn = 'postgresql://postgres:postgres@postgres:5432/postgres'
    db_dsn = 'postgresql://postgres:postgres@postgres:5432/{}'.format(name)

    pg_engine = sqlalchemy.create_engine(pg_dsn)
    pg_engine.raw_connection()\
        .set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    pg_engine.execute('CREATE DATABASE {0}'.format(name))
    pg_engine.dispose()

    db_engine = sqlalchemy.create_engine(db_dsn)
    setup_db(db_engine)
    db_engine.dispose()

    def fin():
        pg_engine = sqlalchemy.create_engine(pg_dsn)
        pg_engine.raw_connection() \
            .set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        pg_engine.execute('DROP DATABASE {0}'.format(name))
        pg_engine.dispose()

    request.addfinalizer(fin)
    return db_dsn


@pytest.fixture(autouse=True)
def fixture_setter(request, _db_dsn):
    request.instance.db_dsn = _db_dsn


@pytest.mark.usefixtures('fixture_setter')
class TestSourceAIOPG(SourceSQLAlchemyTestBase):

    @cached_property
    def queries(self):
        return get_queries(hiku.sources.aiopg, SA_ENGINE_KEY, AsyncQueries)

    async def _check(self, src, value, event_loop):
        sa_engine = await aiopg.sa.create_engine(self.db_dsn, minsize=0,
                                                 loop=event_loop)
        try:
            engine = Engine(AsyncIOExecutor(event_loop))
            result = await engine.execute(self.graph, read(src),
                                          {SA_ENGINE_KEY: sa_engine})
            check_result(result, value)
        finally:
            sa_engine.close()
            await sa_engine.wait_closed()

    def check(self, src, value):
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        asyncio.set_event_loop_policy(ForbiddenEventLoopPolicy())
        try:
            loop.run_until_complete(self._check(src, value, loop))
        finally:
            loop.close()
            asyncio.set_event_loop_policy(policy)
