from types import SimpleNamespace
from typing import NamedTuple
import pytest

from hiku.utils import listify
from hiku.graph import Graph, Link, Node, Option, Root, Field
from hiku.types import (
    Integer,
    String,
    TypeRef,
    Sequence,
)
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import read
from hiku.endpoint.graphql import _StripQuery, GraphQLEndpoint
from hiku.endpoint.graphql import BatchGraphQLEndpoint, AsyncGraphQLEndpoint
from hiku.endpoint.graphql import AsyncBatchGraphQLEndpoint
from hiku.executors.asyncio import AsyncIOExecutor


def test_strip():
    query = read("""
    query {
        __typename
        foo {
            __typename
            bar {
                __typename
                baz
            }
        }
    }
    """)
    assert _StripQuery().visit(query) == read("""
    query {
        foo {
            bar {
                baz
            }
        }
    }
    """)


@pytest.fixture(name='sync_graph')
def sync_graph_fixture():
    def answer(fields):
        return ['42' for _ in fields]
    return Graph([Root([Field('answer', String, answer)])])


class Product(NamedTuple):
    id: int
    name: str
    company_id: int


class Company(NamedTuple):
    id: int
    name: str


DB = {
    'products': {
        1: Product(id=1, name='iphone 10', company_id=10),
        2: Product(id=2, name='windows phone', company_id=20),
        3: Product(id=3, name='iphone 5', company_id=10),
    },
    'companies': {
        10: Company(id=10, name='apple'),
        20: Company(id=20, name='microsoft'),
    },
}


@pytest.fixture(name='sync_graph_complex')
def sync_graph_complex_fixture():
    @listify
    def company_fields_resolver(fields, data_list):
        def get_field(f, data):
            if f.name == 'id':
                return data.id
            if f.name == 'name':
                return data.name
            raise Exception(f'Unknown field {f}')

        return [[get_field(f, data) for f in fields] for data in data_list]

    @listify
    def link_company(ids):
        print('\nlink company by ids', ids)
        for id_ in ids:
            yield DB['companies'][id_]

    @listify
    def product_fields_resolver(fields, ids):
        def get_field(f, product):
            if f.name == 'id':
                return product.id
            if f.name == 'name':
                return product.name
            if f.name == 'company_id':
                return product.company_id
            raise Exception(f'Unknown field {f}')

        for id_ in ids:
            yield [get_field(f, DB['products'][id_]) for f in fields]

    def link_product(opts):
        return opts['id']

    def link_products():
        return [id_ for id_ in DB['products'].keys()]

    return Graph([
        Node('company', [
            Field('id', Integer, company_fields_resolver),
            Field('name', String, company_fields_resolver),
        ]),
        Node('product', [
            Field('id', Integer, product_fields_resolver),
            Field('name', String, product_fields_resolver),
            Field('company_id', Integer, product_fields_resolver),
            Link('company', TypeRef['company'], link_company, requires='company_id')
        ]),
        Root([
            Link(
                'product',
                TypeRef['product'],
                link_product,
                options=[
                    Option('id', Integer),
                ],
                requires=None
            ),
            Link(
                'products',
                Sequence[TypeRef['product']],
                link_products,
                requires=None
            )
        ])
    ])


def test_endpoint_many_cached(sync_graph_complex):
    endpoint = GraphQLEndpoint(Engine(SyncExecutor()), sync_graph_complex)
    query = """
    query Products {
        products {
            id
            name
            company @cached(ttl: 10) {
                id
                name
            }
        }
    }
    """
    result = endpoint.dispatch({'query': query})
    assert result == {'data': {
        'products': [{
            'id': 1,
            'name': 'iphone 10',
            'company': {
                'id': 10,
                'name': 'apple',
            }
        }, {
            'id': 2,
            'name': 'windows phone',
            'company': {
                'id': 20,
                'name': 'microsoft',
            }
        }, {
            'id': 3,
            'name': 'iphone 5',
            'company': {
                'id': 10,
                'name': 'apple',
            }
        }]
    }}


def test_endpoint_cached(sync_graph_complex):
    endpoint = GraphQLEndpoint(Engine(SyncExecutor()), sync_graph_complex)
    def get_query(product_id: int) -> str:
        return """
        query Product {
            product(id: %s) {
                id
                name
                company @cached(ttl: 10) {
                    id
                    name
                }
            }
        }
        """ % product_id

    result = endpoint.dispatch({'query': get_query(1)})
    assert result == {'data': {
        'product': {
            'id': 1,
            'name': 'iphone 10',
            'company': {
                'id': 10,
                'name': 'apple',
            }
        }
    }}
    result = endpoint.dispatch({'query': get_query(2)})
    assert result == {'data': {
        'product': {
            'id': 2,
            'name': 'windows phone',
            'company': {
                'id': 20,
                'name': 'microsoft',
            }
        }
    }}
    result = endpoint.dispatch({'query': get_query(3)})
    # cached company
    assert result == {'data': {
        'product': {
            'id': 3,
            'name': 'iphone 5',
            'company': {
                'id': 10,
                'name': 'apple',
            }
        }
    }}


@pytest.fixture(name='async_graph')
def async_graph_fixture():
    async def answer(fields):
        return ['42' for _ in fields]
    return Graph([Root([Field('answer', String, answer)])])


def test_endpoint(sync_graph):
    endpoint = GraphQLEndpoint(Engine(SyncExecutor()), sync_graph)
    result = endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}


def test_batch_endpoint(sync_graph):
    endpoint = BatchGraphQLEndpoint(Engine(SyncExecutor()), sync_graph)

    assert endpoint.dispatch([]) == []

    result = endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}

    batch_result = endpoint.dispatch([
        {'query': '{answer}'},
        {'query': '{__typename}'},
    ])
    assert batch_result == [
        {'data': {'answer': '42'}},
        {'data': {'__typename': 'Query'}},
    ]


@pytest.mark.asyncio
async def test_async_endpoint(async_graph):
    endpoint = AsyncGraphQLEndpoint(Engine(AsyncIOExecutor()), async_graph)
    result = await endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}


@pytest.mark.asyncio
async def test_async_batch_endpoint(async_graph):
    endpoint = AsyncBatchGraphQLEndpoint(Engine(AsyncIOExecutor()), async_graph)

    assert await endpoint.dispatch([]) == []

    result = await endpoint.dispatch({'query': '{answer}'})
    assert result == {'data': {'answer': '42'}}

    batch_result = await endpoint.dispatch([
        {'query': '{answer}'},
        {'query': '{__typename}'},
    ])
    assert batch_result == [
        {'data': {'answer': '42'}},
        {'data': {'__typename': 'Query'}},
    ]
