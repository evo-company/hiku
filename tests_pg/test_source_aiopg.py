import pytest
import asyncio
import aiopg.sa

import hiku.sources.aiopg

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
        fields_query_cls=hiku.sources.aiopg.FieldsQuery,
        link_query_cls=hiku.sources.aiopg.LinkQuery,
    )
    request.cls.graph = graph


@pytest.fixture(scope='class', name='db_dsn_attr')
def db_dsn_fixture(request, db_dsn):
    request.cls.db_dsn = db_dsn


@pytest.mark.usefixtures('graph_attr', 'db_dsn_attr')
class TestSourceAIOPG(SourceSQLAlchemyTestBase):

    async def _check(self, src, value):
        sa_engine = await aiopg.sa.create_engine(self.db_dsn, minsize=0)
        engine = Engine(AsyncIOExecutor())
        try:
            result = await engine.execute(
                read(src), self.graph, ctx={SA_ENGINE_KEY: sa_engine}
            )
            check_result(result, value)
        finally:
            sa_engine.close()
            await sa_engine.wait_closed()

    def check(self, src, value):
        asyncio.get_event_loop().run_until_complete(self._check(src, value))
