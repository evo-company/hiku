import asyncio

from aiohttp import web

from hiku.types import String
from hiku.graph import Graph, Root, Field, apply
from hiku.engine import Engine
from hiku.result import denormalize
from hiku.validate.query import validate
from hiku.readers.graphql import read
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.introspection.graphql import AsyncGraphQLIntrospection


async def foo_field_func(fields):
    return ['Hello World!']


GRAPH = Graph([
    Root([
        Field('foo', String, foo_field_func),
    ]),
])


async def handler(request):
    hiku_engine = request.app['HIKU_ENGINE']
    data = await request.json()
    try:
        query = read(data['query'], data.get('variables'))
        errors = validate(request.app['GRAPH'], query)
        if errors:
            result = {'errors': [{'message': e} for e in errors]}
        else:
            result = await hiku_engine.execute(request.app['GRAPH'], query)
            result = {'data': denormalize(request.app['GRAPH'], result, query)}
    except Exception as err:
        result = {'errors': [{'message': repr(err)}]}
    return web.json_response(result)


if __name__ == "__main__":
    app = web.Application()
    app.router.add_post('/', handler)
    app['HIKU_ENGINE'] = Engine(AsyncIOExecutor(asyncio.get_event_loop()))
    app['GRAPH'] = apply(GRAPH, [AsyncGraphQLIntrospection()])
    web.run_app(app)
