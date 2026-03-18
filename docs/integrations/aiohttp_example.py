from aiohttp import web

from hiku.types import String
from hiku.graph import Graph, Root, Field
from hiku.engine import Engine
from hiku.endpoint.graphql import AsyncGraphQLEndpoint
from hiku.executors.asyncio import AsyncIOExecutor


def say_hello(fields):
    return ['Hello World!' for _ in fields]


QUERY_GRAPH = Graph([
    Root([Field('hello', String, say_hello)]),
])


async def handle_graphql(request):
    data = await request.json()
    context = {
        'redis': request.app['redis'],
    }
    result = await request.app['graphql-endpoint'].dispatch(data, context)
    return web.json_response(result)


if __name__ == "__main__":
    app = web.Application()
    app.add_routes([
        web.post('/graphql', handle_graphql),
    ])
    app['graphql-endpoint'] = AsyncGraphQLEndpoint(
        Engine(AsyncIOExecutor()), QUERY_GRAPH
    )
    app['redis'] = Redis()
    web.run_app(app, host='0.0.0.0', port=5000)
