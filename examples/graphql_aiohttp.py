import asyncio
import logging
import functools

from aiohttp import web

from hiku.types import String, Boolean, Integer, TypeRef, Record
from hiku.graph import Graph, Root, Field, apply, Option
from hiku.engine import Engine
from hiku.result import denormalize
from hiku.validate.query import validate
from hiku.readers.graphql import read_operation, OperationType
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.introspection.graphql import AsyncGraphQLIntrospection


log = logging.getLogger(__name__)


def listify(func):
    """Just an utility function to use generators to return result"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return [i async for i in func(*args, **kwargs)]
    return wrapper


@listify
async def value_func(fields):
    for _ in fields:
        yield 'Hello World!'


@listify
async def action_func(fields):
    for field in fields:
        print('action performed!', field.options)
        yield True


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


async def execute(engine, graph, query, ctx=None):
    errors = validate(graph, query)
    if not errors:
        result = await engine.execute(graph, query, ctx=ctx)
        return {'data': denormalize(graph, result)}
    else:
        return {'errors': errors}


async def dispatch(data, engine, query_graph, mutation_graph, ctx=None):
    try:
        op = read_operation(data['query'],
                            variables=data.get('variables'),
                            operation_name=data.get('operationName'))
        if op.type is OperationType.QUERY:
            return await execute(engine, query_graph, op.query, ctx=ctx)
        elif op.type is OperationType.MUTATION:
            return await execute(engine, mutation_graph, op.query, ctx=ctx)
        else:
            return {'errors': [{'message': ('Unsupported operation type: {!r}'
                                            .format(op.type))}]}
    except Exception:
        log.exception('Failed to execute GraphQL query')
        return {'errors': [{'message': 'Failed to execute GraphQL query'}]}


async def handler(request):
    data = await request.json()

    engine = request.app['hiku_engine']
    graphs = (request.app['query_graph'],
              request.app['mutation_graph'])
    ctx = {}

    batch = data if isinstance(data, list) else [data]
    batch_result = [await dispatch(i, engine, *graphs, ctx=ctx) for i in batch]
    result_data = batch_result if isinstance(data, list) else batch_result[0]
    return web.json_response(result_data)


if __name__ == "__main__":
    logging.basicConfig()

    app = web.Application()
    app.router.add_post('/graphql', handler)

    introspection = AsyncGraphQLIntrospection(QUERY_GRAPH, MUTATION_GRAPH)
    app['hiku_engine'] = Engine(AsyncIOExecutor(asyncio.get_event_loop()))
    app['query_graph'] = apply(QUERY_GRAPH, [introspection])
    app['mutation_graph'] = apply(MUTATION_GRAPH, [introspection])

    web.run_app(app)
