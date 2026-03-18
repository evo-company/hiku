from hiku.types import String
from hiku.graph import Graph, Root, Field
from hike.schema import Schema
from hiku.endpoint.graphql import AsyncGraphQLEndpoint
from hiku.executors.asyncio import AsyncIOExecutor

async def say_hello(fields):
    return ['Hello World!' for _ in fields]

QUERY_GRAPH = Graph([
    Root([Field('hello', String, say_hello)]),
])

schema = Schema(AsyncIOExecutor(), QUERY_GRAPH)

endpoint = AsyncGraphQLEndpoint(schema)

assert await endpoint.dispatch({
    'query': "{ hello }",
    'variables': None,
    'operationName': "GetHello",
}) == {
   'data': {
       'hello': 'Hello World!',
   },
}
