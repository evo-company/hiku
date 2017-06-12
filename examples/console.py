from wsgiref.simple_server import make_server

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from hiku.engine import Engine
from hiku.sources import sqlalchemy as sa
from hiku.console.ui import ConsoleApplication
from hiku.executors.sync import SyncExecutor

from tests.test_source_sqlalchemy import SA_ENGINE_KEY, SyncQueries, setup_db
from tests.test_source_sqlalchemy import get_queries, get_graph


if __name__ == '__main__':
    engine = Engine(SyncExecutor())

    sa_engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    setup_db(sa_engine)

    graph = get_graph(get_queries(sa, SA_ENGINE_KEY, SyncQueries))

    app = ConsoleApplication(graph, engine, {SA_ENGINE_KEY: sa_engine},
                             debug=True)
    http_server = make_server('localhost', 5000, app)
    http_server.serve_forever()
