from flask import Flask, request, jsonify

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import hiku.sources.sqlalchemy

from hiku.graph import apply
from hiku.engine import Engine
from hiku.result import denormalize
from hiku.executors.sync import SyncExecutor
from hiku.validate.query import validate
from hiku.readers.graphql import read
from hiku.introspection.graphql import GraphQLIntrospection

from tests.test_source_sqlalchemy import setup_db, get_graph, get_queries
from tests.test_source_sqlalchemy import SA_ENGINE_KEY, SyncQueries


app = Flask(__name__)


@app.route('/', methods=['POST'])
def handler():
    hiku_engine = app.config['HIKU_ENGINE']
    data = request.get_json()
    try:
        query = read(data['query'], data.get('variables'))
        errors = validate(app.config['GRAPH'], query)
        if errors:
            result = {'errors': [{'message': e} for e in errors]}
        else:
            result = hiku_engine.execute(app.config['GRAPH'],
                                         query,
                                         ctx=app.config['HIKU_CTX'])
            result = {'data': denormalize(app.config['GRAPH'], result, query)}
    except Exception as err:
        result = {'errors': [{'message': repr(err)}]}
    return jsonify(result)


if __name__ == "__main__":
    sa_engine = create_engine('sqlite://',
                              connect_args={'check_same_thread': False},
                              poolclass=StaticPool)
    setup_db(sa_engine)

    app.config['HIKU_ENGINE'] = Engine(SyncExecutor())
    app.config['HIKU_CTX'] = {SA_ENGINE_KEY: sa_engine}

    graph = get_graph(get_queries(hiku.sources.sqlalchemy, SA_ENGINE_KEY,
                                  SyncQueries))
    graph = apply(graph, [GraphQLIntrospection()])
    app.config['GRAPH'] = graph

    app.run()
