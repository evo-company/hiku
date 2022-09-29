import typing as t

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import (
    Mock,
    call,
)

import pytest
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer as SaInteger,
    Unicode,
    ForeignKey,
    create_engine,
)
from sqlalchemy.pool import StaticPool

from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.executors.threads import ThreadsExecutor
from hiku.expr.core import (
    define,
    S,
)
from hiku.query import _compute_hash
from hiku.result import Reference
from hiku.sources.graph import SubGraph
from hiku.sources.sqlalchemy import (
    FieldsQuery,
    LinkQuery,
)
from hiku.graph import Graph, Link, Node, Option, Root, Field
from hiku.types import (
    Integer,
    String,
    TypeRef,
    Sequence,
    Record,
    Any,
)
from hiku.engine import Engine
from hiku.readers.graphql import read
from hiku.cache import BaseCache, get_query_hash


class InMemoryCache(BaseCache):
    def __init__(self) -> None:
        self._store: t.Dict[str, t.Any] = {}

    def get_many(self, keys: t.List[str]) -> t.Dict[str, t.Any]:
        result = {}
        for key in keys:
            if key in self._store:
                result[key] = self._store[key]
        return result

    def set_many(self, items: t.Dict[str, t.Any], ttl: int) -> None:
        self._store.update(items)


SA_ENGINE_KEY = 'sa-engine'
metadata = MetaData()

thread_pool = ThreadPoolExecutor(2)

product_table = Table(
    'product',
    metadata,
    Column('id', SaInteger, primary_key=True, autoincrement=True),
    Column('name', Unicode),
    Column('company_id', ForeignKey('company.id')),
)

attribute_table = Table(
    'attribute',
    metadata,
    Column('id', SaInteger, primary_key=True, autoincrement=True),
    Column('product_id', SaInteger),
    Column('name', Unicode),
)

attribute_value_table = Table(
    'attribute_value',
    metadata,
    Column('id', SaInteger, primary_key=True, autoincrement=True),
    Column('attr_id', SaInteger),
    Column('name', Unicode),
)

company_table = Table(
    'company',
    metadata,
    Column('id', SaInteger, primary_key=True, autoincrement=True),
    Column('owner_id', SaInteger),
    Column('name', Unicode),
)


user_table = Table(
    'users',
    metadata,
    Column('id', SaInteger, primary_key=True, autoincrement=True),
    Column('company_id', SaInteger),
    Column('username', Unicode),
)


def setup_db(db_engine):
    metadata.create_all(db_engine)
    for r in [c._asdict() for c in DB['companies'].values()]:
        db_engine.execute(company_table.insert(), r)
    for r in [c._asdict() for c in DB['users'].values()]:
        db_engine.execute(user_table.insert(), r)
    for r in [p._asdict() for p in DB['attributes'].values()]:
        db_engine.execute(attribute_table.insert(), r)
    for r in [p._asdict() for p in DB['attribute_values'].values()]:
        db_engine.execute(attribute_value_table.insert(), r)
    for r in [p._asdict() for p in DB['products'].values()]:
        db_engine.execute(product_table.insert(), r)


class Product(t.NamedTuple):
    id: int
    name: str
    company_id: int


class Attribute(t.NamedTuple):
    id: int
    name: str
    product_id: int


class AttributeValue(t.NamedTuple):
    id: int
    name: str
    attr_id: int


class Company(t.NamedTuple):
    id: int
    name: str
    owner_id: int


class User(t.NamedTuple):
    id: int
    company_id: int
    username: str


DB = {
    'products': {
        1: Product(id=1, name='iphone 10', company_id=10),
        2: Product(id=2, name='windows phone', company_id=20),
        3: Product(id=3, name='iphone 5', company_id=10),
    },
    'attributes': {
      11: Attribute(id=11, product_id=1, name='color'),
      12: Attribute(id=12, product_id=1, name='year'),
    },
    'attribute_values': {
        111: AttributeValue(id=111, attr_id=11, name='red'),
        112: AttributeValue(id=112, attr_id=11, name='blue'),
    },
    'companies': {
        10: Company(id=10, name='apple', owner_id=100),
        20: Company(id=20, name='microsoft', owner_id=200),
    },
    'users': {
        100: User(id=100, company_id=10, username='steve'),
        200: User(id=200, company_id=20, username='bill'),
    },
}


def direct_link(ids):
    return ids


def link_user(opts):
    return opts['id']


def link_company(opts):
    return opts['id']


def link_product(opts):
    return DB['products'][opts['id']]


def link_products():
    return [p for p in DB['products'].values()]


def link_product_attributes(ids):
    attributes = DB['attributes']
    reqs = []
    for id_ in ids:
        reqs.append([at.id for at in attributes.values()
                     if at.product_id == id_])

    return reqs


def link_attribute_values(ids):
    attribute_values = DB['attribute_values']
    reqs = []
    for id_ in ids:
        reqs.append([at.id for at in attribute_values.values()
                     if at.attr_id == id_])

    return reqs


ROOT = Root([
    Link(
        'product',
        TypeRef['Product'],
        link_product,
        options=[
            Option('id', Integer),
        ],
        requires=None
    ),
    Link(
        'company',
        TypeRef['Company'],
        link_company,
        options=[
            Option('id', Integer),
        ],
        requires=None
    ),
    Link(
        'user',
        TypeRef['User'],
        link_user,
        options=[
            Option('id', Integer),
        ],
        requires=None
    ),
    Link(
        'products',
        Sequence[TypeRef['Product']],
        link_products,
        requires=None
    ),
])


@pytest.fixture(name='sync_low_level_graph_sqlalchemy')
def sync_low_level_graph_sqlalchemy_fixture():
    user_query = FieldsQuery(SA_ENGINE_KEY, user_table)
    company_query = FieldsQuery(SA_ENGINE_KEY, company_table)
    attribute_query = FieldsQuery(SA_ENGINE_KEY, attribute_table)
    attribute_value_query = FieldsQuery(SA_ENGINE_KEY, attribute_value_table)
    product_query = FieldsQuery(SA_ENGINE_KEY, product_table)

    to_company_query = LinkQuery(
        SA_ENGINE_KEY,
        from_column=company_table.c.id,
        to_column=company_table.c.id,
    )

    to_user_query = LinkQuery(
        SA_ENGINE_KEY,
        from_column=user_table.c.id,
        to_column=user_table.c.id,
    )

    to_attribute_query = LinkQuery(
        SA_ENGINE_KEY,
        from_column=attribute_table.c.product_id,
        to_column=attribute_table.c.id,
    )

    to_attribute_values_query = LinkQuery(
        SA_ENGINE_KEY,
        from_column=attribute_value_table.c.attr_id,
        to_column=attribute_value_table.c.id,
    )

    return Graph([
        Node('User', [
            Field('id', Integer, user_query),
            Field('company_id', Integer, user_query),
            Field('username', String, user_query),
        ]),
        Node('Company', [
            Field('id', Integer, company_query),
            Field('name', String, company_query),
            Field('owner_id', Integer, company_query),
            Link('owner', TypeRef['User'], to_user_query, requires='owner_id')
        ]),
        Node('AttributeValue', [
           Field('id', Integer, attribute_value_query),
           Field('name', String, attribute_value_query),
        ]),
        Node('Attribute', [
           Field('id', Integer, attribute_query),
           Field('name', String, attribute_query),
           Link('values', Sequence[TypeRef['AttributeValue']],
                to_attribute_values_query, requires='id')
        ]),
        Node('Product', [
            Field('id', Integer, product_query),
            Field('name', String, product_query),
            Field('company_id', Integer, product_query),
            Link('attributes', Sequence[TypeRef['Attribute']],
                 to_attribute_query, requires='id'),
            Link('company', TypeRef['Company'], to_company_query,
                 requires='company_id')
        ]),
    ])


data_types = {
    'Address': Record[{
        'city': String,
    }]
}


@pytest.fixture(name='sync_high_level_graph_sqlalchemy')
def sync_high_level_graph_fixture(sync_low_level_graph_sqlalchemy):
    """This graph covers all cases of data access.

    - Product -> Company link
    - Product -> Attribute - sequence link
    - Company -> Address - record link
    - User.photo - field with options
    - Company -> Owner - link with owner_id as requires
    """
    low_level_graph = sync_low_level_graph_sqlalchemy

    company_sg = SubGraph(low_level_graph, 'Company')
    attribute_sg = SubGraph(low_level_graph, 'Attribute')
    attribute_value_sg = SubGraph(low_level_graph, 'AttributeValue')
    user_sg = SubGraph(low_level_graph, 'User')

    def get_photo(fields, ids):
        def get_field(f):
            if f.name == 'photo':
                size = f.options['size']
                return f'https://example.com/photo.jpg?size={size}'

        return [[get_field(f) for f in fields] for _ in ids]

    @define(Record[{'id': Integer}])
    def get_address(company):
        return {
            'city': 'Kyiv'
        }

    def resolve_product_fields(fields, products):
        def get_field(field, product):
            if field.name == 'id':
                return product.id
            elif field.name == 'name':
                return product.name
            elif field.name == 'company_id':
                return product.company_id
            elif field.name == '_attributes':
                return [
                    at.id for at in DB['attributes'].values()
                    if at.product_id == product.id
                ]

        return [[get_field(f, p) for f in fields] for p in products]

    return Graph([
        Node('User', [
            Field('id', Integer, user_sg),
            Field('company_id', Integer, user_sg),
            Field('username', String, user_sg),
            Field('photo', String, get_photo, options=[
                Option('size', Integer),
            ]),
        ]),
        Node('Company', [
            Field('id', Integer, company_sg),
            Field('name', String, company_sg),
            Field('owner_id', Integer, company_sg),
            Field('address', TypeRef['Address'],
                  company_sg.c(get_address(S.this))),
            Link('owner', TypeRef['User'], direct_link, requires='owner_id')
        ]),
        Node('AttributeValue', [
           Field('id', Integer, attribute_value_sg),
           Field('name', String, attribute_value_sg),
        ]),
        Node('Attribute', [
           Field('id', Integer, attribute_sg),
           Field('name', String, attribute_sg),
           Link('values', Sequence[TypeRef['AttributeValue']],
                link_attribute_values, requires='id')
        ]),
        Node('Product', [
            Field('id', Integer, resolve_product_fields),
            Field('name', String, resolve_product_fields),
            Field('company_id', Integer, resolve_product_fields),
            Field('_attributes', Sequence[Any], resolve_product_fields),
            Link('attributes', Sequence[TypeRef['Attribute']],
                 direct_link,
                 requires='_attributes'),
            Link('company', TypeRef['Company'], direct_link,
                 requires='company_id')
        ]),
        ROOT
    ])


@pytest.fixture(name='sync_graph_sqlalchemy')
def sync_graph_sqlalchemy_fixture(sync_high_level_graph_sqlalchemy):
    low_level = sync_high_level_graph_sqlalchemy

    return Graph([
        *low_level.nodes,
        ROOT
    ], data_types=data_types)


def get_product_query(product_id: int) -> str:
    return """
    query Product {
        product(id: %s) {
            id
            name
            attributes @cached(ttl: 15) {
                id
                name
                values {
                    id
                    name
                }
            }
            company  @cached(ttl: 10) {
                id
                name
                address { city }
                owner {
                    username
                    photo(size: 50)
                }
            }
        }
    }
    """ % product_id


def get_products_query() -> str:
    return """
    query Products {
        products {
            id
            name
            attributes @cached(ttl: 15) {
                id
                name
                values {
                    id
                    name
                }
            }
            company @cached(ttl: 10) {
                id
                name
                address { city }
                owner {
                    username
                    photo(size: 50)
                }
            }
        }
    }
    """


def assert_dict_equal(got, exp):
    assert _compute_hash(got) == _compute_hash(exp)


def test_cached_link_one__sqlalchemy(sync_graph_sqlalchemy):
    graph = sync_graph_sqlalchemy
    sa_engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    setup_db(sa_engine)

    cache = InMemoryCache()
    cache = Mock(wraps=cache)
    engine = Engine(ThreadsExecutor(thread_pool), cache)

    def execute(q):
        proxy = engine.execute(graph, q, {SA_ENGINE_KEY: sa_engine})
        return DenormalizeGraphQL(graph, proxy, 'query').process(q)

    query = read(get_product_query(1))
    company_link = query.fields_map['product'].node.fields_map['company']
    attributes_link = query.fields_map['product'].node.fields_map['attributes']

    photo_field = (
        query.fields_map['product']
        .node.fields_map['company']
        .node.fields_map['owner']
        .node.fields_map['photo']
    )

    company_key = get_query_hash(company_link, 10)
    attributes_key = get_query_hash(attributes_link, [11, 12])

    company_cache = {
        'User': {
            100: {
                'username': 'steve',
                photo_field.index_key: 'https://example.com/photo.jpg?size=50'
            }
        },
        'Company': {
            10: {
                'id': 10,
                'name': 'apple',
                'address': {'city': 'Kyiv'},
                'owner': Reference('User', 100)
            },
        },
        'Product': {'company': Reference('Company', 10)}
    }

    attributes_cache = {
        'AttributeValue': {
            111: {'id': 111, 'name': 'red'},
            112: {'id': 112, 'name': 'blue'}
        },
        'Attribute': {
            11: {'id': 11, 'name': 'color', 'values': [
                Reference('AttributeValue', 111),
                Reference('AttributeValue', 112),
            ]},
            12: {'id': 12, 'name': 'year', 'values': []},
        },
        'Product': {'attributes': [
            Reference('Attribute', 11), Reference('Attribute', 12)
        ]}
    }

    expected_result = {
        'product': {
            'id': 1,
            'name': 'iphone 10',
            'attributes': [
                {
                    'id': 11,
                    'name': 'color',
                    'values': [
                        {'id': 111, 'name': 'red'},
                        {'id': 112, 'name': 'blue'},
                    ]
                },
                {
                    'id': 12,
                    'name': 'year',
                    'values': []
                }
            ],
            'company': {
                'id': 10,
                'name': 'apple',
                'address': {'city': 'Kyiv'},
                'owner': {
                    'username': 'steve',
                    'photo': 'https://example.com/photo.jpg?size=50'
                }
            }
        }
    }
    assert execute(query) == expected_result

    assert cache.get_many.call_count == 2

    calls = {
        **cache.set_many.mock_calls[0][1][0],
        **cache.set_many.mock_calls[1][1][0]
    }
    assert_dict_equal(calls, {
        attributes_key: attributes_cache,
        company_key: company_cache
    })

    cache.reset_mock()

    assert execute(query) == expected_result
    cache.get_many.assert_has_calls([
        call([attributes_key]),
        call([company_key]),
    ])
    cache.set_many.assert_not_called()


def test_cached_link_many__sqlalchemy(sync_graph_sqlalchemy):
    graph = sync_graph_sqlalchemy
    sa_engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    setup_db(sa_engine)

    cache = InMemoryCache()
    cache = Mock(wraps=cache)
    engine = Engine(ThreadsExecutor(thread_pool), cache)

    def execute(q):
        proxy = engine.execute(graph, q, {SA_ENGINE_KEY: sa_engine})
        return DenormalizeGraphQL(graph, proxy, 'query').process(q)

    query = read(get_products_query())

    company_link = query.fields_map['products'].node.fields_map['company']
    attributes_link = query.fields_map['products'].node.fields_map['attributes']

    photo_field = (
        query.fields_map['products']
        .node.fields_map['company']
        .node.fields_map['owner']
        .node.fields_map['photo']
    )

    company10_key = get_query_hash(company_link, 10)
    company20_key = get_query_hash(company_link, 20)
    attributes11_12_key = get_query_hash(attributes_link, [11, 12])
    attributes_none_key = get_query_hash(attributes_link, [])

    company10_cache = {
        'User': {
            100: {
                'username': 'steve',
                photo_field.index_key: 'https://example.com/photo.jpg?size=50'
            }
        },
        'Company': {
            10: {
                'id': 10,
                'name': 'apple',
                'address': {'city': 'Kyiv'},
                'owner': Reference('User', 100)
            },
        },
        'Product': {'company': Reference('Company', 10)}
    }
    company20_cache = {
        'User': {
            200: {
                'username': 'bill',
                photo_field.index_key: 'https://example.com/photo.jpg?size=50'
            }
        },
        'Company': {
            20: {
                'id': 20,
                'name': 'microsoft',
                'address': {'city': 'Kyiv'},
                'owner': Reference('User', 200)
            },
        },
        'Product': {'company': Reference('Company', 20)}
    }

    attributes11_12_cache = {
        'AttributeValue': {
            111: {'id': 111, 'name': 'red'},
            112: {'id': 112, 'name': 'blue'}
        },
        'Attribute': {
            11: {'id': 11, 'name': 'color', 'values': [
                Reference('AttributeValue', 111),
                Reference('AttributeValue', 112),
            ]},
            12: {'id': 12, 'name': 'year', 'values': []},
        },
        'Product': {'attributes': [
            Reference('Attribute', 11), Reference('Attribute', 12)
        ]}
    }
    attributes_none_cache = {
        'Product': {'attributes': []}
    }

    expected_result = {
        'products': [{
            'id': 1,
            'name': 'iphone 10',
            'attributes': [
                {
                    'id': 11,
                    'name': 'color',
                    'values': [
                        {'id': 111, 'name': 'red'},
                        {'id': 112, 'name': 'blue'},
                    ]
                },
                {
                    'id': 12,
                    'name': 'year',
                    'values': []
                }
            ],
            'company': {
                'id': 10,
                'name': 'apple',
                'address': {'city': 'Kyiv'},
                'owner': {
                    'username': 'steve',
                    'photo': 'https://example.com/photo.jpg?size=50'
                }
            }
        }, {
            'id': 2,
            'name': 'windows phone',
            'attributes': [],
            'company': {
                'id': 20,
                'name': 'microsoft',
                'address': {'city': 'Kyiv'},
                'owner': {
                    'username': 'bill',
                    'photo': 'https://example.com/photo.jpg?size=50'
                }
            }
        }, {
            'id': 3,
            'name': 'iphone 5',
            'attributes': [],
            'company': {
                'id': 10,
                'name': 'apple',
                'address': {'city': 'Kyiv'},
                'owner': {
                    'username': 'steve',
                    'photo': 'https://example.com/photo.jpg?size=50'
                }
            }
        }]
    }

    assert execute(query) == expected_result

    assert cache.get_many.call_count == 2
    calls = {
        **cache.set_many.mock_calls[0][1][0],
        **cache.set_many.mock_calls[1][1][0]
    }
    assert_dict_equal(calls, {
        attributes11_12_key: attributes11_12_cache,
        attributes_none_key: attributes_none_cache,
        company10_key: company10_cache,
        company20_key: company20_cache,
    })

    cache.reset_mock()

    assert execute(query) == expected_result
    assert set(*cache.get_many.mock_calls[0][1]) == {
        attributes11_12_key, attributes_none_key
    }
    assert set(*cache.get_many.mock_calls[1][1]) == {
        company10_key, company20_key
    }

    cache.set_many.assert_not_called()
