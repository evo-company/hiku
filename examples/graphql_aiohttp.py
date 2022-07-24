import logging

from aiohttp import web

from hiku.types import String, Boolean, Integer, TypeRef, Record
from hiku.graph import Graph, Root, Field, Option
from hiku.engine import Engine
from hiku.endpoint.graphql import AsyncGraphQLEndpoint
from hiku.executors.asyncio import AsyncIOExecutor


log = logging.getLogger(__name__)


async def value_func(fields):
    return ['Hello World!' for _ in fields]


async def action_func(fields):
    results = []
    for field in fields:
        print('action performed!', field.options)
        results.append(True)
    return results


DATA_TYPES = {
    'Point': Record[{
        'x': Integer,
        'y': Integer,
    }],
    'Data': Record[{
        'point': TypeRef['Point'],
    }],
}

QUERY_GRAPH = Graph([
    Root([
        Field('value', String, value_func),
    ]),
], data_types=DATA_TYPES)

MUTATION_GRAPH = Graph(QUERY_GRAPH.nodes + [
    Root([
        Field('action', Boolean, action_func,
              options=[Option('data', TypeRef['Data'])]),
    ]),
], data_types=DATA_TYPES)


async def handle_graphql(request):
    data = await request.json()
    result = await request.app['graphql-endpoint'].dispatch(data)
    return web.json_response(result)


def main():
    logging.basicConfig(level=logging.DEBUG)
    app = web.Application()
    app.add_routes([
        web.post('/graphql', handle_graphql),
    ])
    app['graphql-endpoint'] = AsyncGraphQLEndpoint(
        Engine(AsyncIOExecutor()), QUERY_GRAPH, MUTATION_GRAPH,
    )
    web.run_app(app, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()
