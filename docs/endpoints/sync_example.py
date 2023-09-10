from hiku.graph import Graph, Root, Field
from hiku.types import String
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.endpoint.graphql import GraphQLEndpoint

def say_hello(fields):
    return ['Hello World!' for _ in fields]

QUERY_GRAPH = Graph([
    Root([Field('hello', String, say_hello)]),
])

endpoint = GraphQLEndpoint(
    Engine(SyncExecutor()), QUERY_GRAPH
)

assert endpoint.dispatch({
    'query': "{ hello }",
    'variables': None,
    'operationName': "GetHello",
}) == {
    'data': {
        'hello': 'Hello World!',
    },
}
