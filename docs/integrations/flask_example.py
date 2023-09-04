from flask import Flask, request, jsonify

from hiku.graph import Graph, Root, Field
from hiku.types import String
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.endpoint.graphql import GraphQLEndpoint

app = Flask(__name__)

redis = Redis()

def say_hello(fields):
    return ['Hello World!' for _ in fields]

QUERY_GRAPH = Graph([
    Root([Field('hello', String, say_hello)]),
])

graphql_endpoint = GraphQLEndpoint(
    Engine(SyncExecutor()), QUERY_GRAPH
)

@app.route('/graphql', methods={'POST'})
def graphql():
    data = request.get_json()
    context = {'redis': redis}
    result = graphql_endpoint.dispatch(data, context)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
