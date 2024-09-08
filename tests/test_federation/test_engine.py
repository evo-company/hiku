import pytest
from hiku.graph import Graph, Nothing

import hiku.query
from hiku.executors.asyncio import AsyncIOExecutor
from hiku.federation.endpoint import denormalize_entities
from hiku.federation.engine import Engine
from hiku.federation.validate import validate
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import read

from hiku.graph import (
    Field,
    Link,
    Option,
    Root,
)
from hiku.types import (
    Integer,
    TypeRef,
    Optional,
)

from hiku.federation.graph import FederatedNode, Graph
from hiku.federation.directive import Key

from tests.test_federation.utils import (
    GRAPH,
    ASYNC_GRAPH,
    data_types,
    cart_resolver,
    ids_resolver,
)


def execute(query: hiku.query.Node, graph: Graph, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query, ctx=ctx)


async def execute_async(query: hiku.query.Node, graph: Graph, ctx=None):
    engine = Engine(AsyncIOExecutor())
    return await engine.execute(graph, query, ctx=ctx)


ENTITIES_QUERY = {
    'query': """
        query($representations:[_Any!]!) {
            _entities(representations:$representations) {
                ...on Cart {
                    status { id title }
                }
            }
        }
        """,
    'variables': {
        'representations': [
            {'__typename': 'Cart', 'id': 1},
            {'__typename': 'Cart', 'id': 2},
        ]
    }
}


SDL_QUERY = hiku.query.Node(fields=[
    hiku.query.Link('_service', hiku.query.Node(fields=[hiku.query.Field('sdl')]))
])


def test_validate_entities_query():
    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    errors = validate(GRAPH, query)
    assert errors == []


def test_execute_sync_executor():
    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    result = execute(query, GRAPH)
    data = denormalize_entities(
        GRAPH,
        query,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == data


@pytest.mark.asyncio
async def test_execute_async_executor():
    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    result = await execute_async(query, ASYNC_GRAPH)
    data = denormalize_entities(
        GRAPH,
        query,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        {'status': {'id': 'ORDERED', 'title': 'ordered'}}
    ]
    assert expect == data


def test_resolve_reference_optional():
    """Test when resolve_reference returns Nothing for one of the entities"""

    def resolve_cart(representations):
        # Lets assume that we found only one cart in storage, and the other one
        # is missing so we return Nothing for it
        ids = [r['id'] for r in representations]
        return [ids[0], Nothing]

    _GRAPH = Graph([
        FederatedNode('Cart', [
            Field('id', Integer, cart_resolver),
            Field('status', TypeRef['Status'], cart_resolver),
        ], directives=[Key('id')], resolve_reference=resolve_cart),
        Root([
            Link(
                'cart',
                Optional[TypeRef['Cart']],
                ids_resolver,
                requires=None,
                options=[
                    Option('id', Integer)
                ],
            ),
        ]),
    ], data_types=data_types)

    query = read(ENTITIES_QUERY['query'], ENTITIES_QUERY['variables'])
    result = execute(query, _GRAPH)
    data = denormalize_entities(
        _GRAPH,
        query,
        result,
    )

    expect = [
        {'status': {'id': 'NEW', 'title': 'new'}},
        None
    ]
    assert expect == data
