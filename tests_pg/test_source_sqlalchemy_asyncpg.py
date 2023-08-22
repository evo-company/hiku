import pytest
import asyncio
from sqlalchemy.util import greenlet_spawn
from sqlalchemy.ext.asyncio import create_async_engine

import hiku.sources.sqlalchemy_async

from hiku.engine import Engine
from hiku.readers.simple import read
from hiku.executors.asyncio import AsyncIOExecutor

from tests.base import check_result
from tests.test_source_sqlalchemy import SourceSQLAlchemyTestBase
from tests.test_source_sqlalchemy import graph_factory, SA_ENGINE_KEY


@pytest.fixture(scope='class', name='graph_attr')
def graph_fixture(request):
    graph = graph_factory(
        async_=True,
        fields_query_cls=hiku.sources.sqlalchemy_async.FieldsQuery,
        link_query_cls=hiku.sources.sqlalchemy_async.LinkQuery,
    )
    request.cls.graph = graph


@pytest.fixture(scope='class', name='db_dsn_attr')
def db_dsn_fixture(request, db_dsn):
    request.cls.db_dsn = db_dsn.replace('postgresql://',
                                        'postgresql+asyncpg://')


@pytest.mark.usefixtures('graph_attr', 'db_dsn_attr')
class TestSourceSQLAlchemyAsyncPG(SourceSQLAlchemyTestBase):

    async def _check(self, src, value):
        sa_engine = create_async_engine(self.db_dsn)
        engine = Engine(AsyncIOExecutor())
        try:
            result = await engine.execute_query(
                self.graph, read(src), {SA_ENGINE_KEY: sa_engine}
            )
            check_result(result, value)
        finally:
            await greenlet_spawn(sa_engine.sync_engine.dispose)

    def check(self, src, value):
        asyncio.get_event_loop().run_until_complete(self._check(src, value))
