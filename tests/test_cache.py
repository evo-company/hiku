import typing as t

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import (
    Mock,
    ANY,
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
)
from hiku.engine import (
    Engine,
    get_query_hash,
)
from hiku.readers.graphql import read
from hiku.cache import BaseCache


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
    for r in [p._asdict() for p in DB['products'].values()]:
        db_engine.execute(product_table.insert(), r)


class Product(t.NamedTuple):
    id: int
    name: str
    company_id: int


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
    return opts['id']


def link_products():
    return [id_ for id_ in DB['products'].keys()]


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
    )
])


@pytest.fixture(name='sync_low_level_graph_sqlalchemy')
def sync_low_level_graph_sqlalchemy_fixture():
    user_query = FieldsQuery(SA_ENGINE_KEY, user_table)
    company_query = FieldsQuery(SA_ENGINE_KEY, company_table)
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
        Node('Product', [
            Field('id', Integer, product_query),
            Field('name', String, product_query),
            Field('company_id', Integer, product_query),
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
    low_level_graph = sync_low_level_graph_sqlalchemy

    product_sg = SubGraph(low_level_graph, 'Product')
    company_sg = SubGraph(low_level_graph, 'Company')
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
        Node('Product', [
            Field('id', Integer, product_sg),
            Field('name', String, product_sg),
            Field('company_id', Integer, product_sg),
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


def assert_call_ids(func_mock, ids):
    assert func_mock.call_args[0][1] == ids


def assert_fields_query_call_ids(func_mock, ids):
    assert func_mock.call_args[0][2] == ids


def get_product_query(product_id: int) -> str:
    return """
    query Product {
        product(id: %s) {
            id
            name
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
    """ % product_id


def get_products_query() -> str:
    return """
    query Products {
        products {
            id
            name
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


def get_product_all_query(product_id: int) -> str:
    return """
    query Product {
        product(id: %s) {
            id
            company {
                id
                address { city }
                owner {
                    id
                }
            }
        }
        company(id: 20) {
            name
            address { city }
        }
        user(id: 200) {
           username
           photo(size: 50)
        }
        products {
            id
            company {
                id
                owner {
                    id
                }
            }
        }
    }
    """ % product_id


def assert_cache_set_with(cache, exp):
    assert _compute_hash(cache.set_many.call_args[0][0]) == _compute_hash(exp)


def assert_cache_get_with(cache, exp):
    assert set(cache.get_many.call_args[0][0]) == set(exp)


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
    link = query.fields_map['product'].node.fields_map['company']
    photo_field = (
        query.fields_map['product']
        .node.fields_map['company']
        .node.fields_map['owner']
        .node.fields_map['photo']
    )
    key = get_query_hash(link, 10)
    expected_cached = {key: {
        'Product': {
            'company': Reference('Company', 10),
        },
        'Company': {
            10: {
                'id': 10,
                'name': 'apple',
                'address': {'city': 'Kyiv'},
                'owner': Reference('User', 100),
            }
        },
        'User': {
            100: {
                'username': 'steve',
                photo_field.index_key: 'https://example.com/photo.jpg?size=50'
            }
        }
    }}
    expected_result = {
        'product': {
            'id': 1,
            'name': 'iphone 10',
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

    assert cache.get_many.call_count == 1
    cache.set_many.assert_called_once_with(ANY, 10)
    assert_cache_set_with(cache, expected_cached)

    cache.reset_mock()

    assert execute(query) == expected_result

    cache.get_many.assert_called_once_with([key])
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
    link = query.fields_map['products'].node.fields_map['company']
    photo_field = (
        query.fields_map['products']
        .node.fields_map['company']
        .node.fields_map['owner']
        .node.fields_map['photo']
    )

    key10 = get_query_hash(link, 10)
    key20 = get_query_hash(link, 20)

    expected_cached = {
        key10: {
            'Product': {
                'company': Reference('Company', 10),
            },
            'Company': {
                10: {
                    'id': 10,
                    'name': 'apple',
                    'address': {'city': 'Kyiv'},
                    'owner': Reference('User', 100),
                }
            },
            'User': {
                100: {
                    'username': 'steve',
                    photo_field.index_key: 'https://example.com/photo.jpg?size=50'  # noqa: E501
                }
            },
        },
        key20: {
            'Product': {
                'company': Reference('Company', 20),
            },
            'Company': {
                20: {
                    'id': 20,
                    'name': 'microsoft',
                    'address': {'city': 'Kyiv'},
                    'owner': Reference('User', 200),
                }
            },
            'User': {
                200: {
                    'username': 'bill',
                    photo_field.index_key: 'https://example.com/photo.jpg?size=50'  # noqa: E501
                }
            },
        }
    }
    expected_result = {
        'products': [{
            'id': 1,
            'name': 'iphone 10',
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

    assert cache.get_many.call_count == 1
    cache.set_many.assert_called_once_with(ANY, 10)
    assert_cache_set_with(cache, expected_cached)

    cache.reset_mock()

    assert execute(query) == expected_result

    cache.get_many.assert_called_once()
    assert_cache_get_with(cache, [key10, key20])
    cache.set_many.assert_not_called()


def test_track_done(sync_graph_sqlalchemy):
    graph = sync_graph_sqlalchemy
    sa_engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    setup_db(sa_engine)

    engine = Engine(ThreadsExecutor(thread_pool))

    def execute(q):
        proxy = engine.execute(graph, q, {SA_ENGINE_KEY: sa_engine})
        return DenormalizeGraphQL(graph, proxy, 'query').process(q)

    query = read(get_product_all_query(1))
    expected_result = {
        'product': {
            'id': 1,
            'company': {
                'id': 10,
                'address': {'city': 'Kyiv'},
                'owner': {
                    'id': 100
                }
            }
        },
        'company': {
            'name': 'microsoft',
            'address': {'city': 'Kyiv'},
        },
        'user': {
            'username': 'bill',
            'photo': 'https://example.com/photo.jpg?size=50'
        },
        'products': [{
            'id': 1,
            'company': {
                'id': 10,
                'owner': {
                    'id': 100
                }
            }
        }, {
            'id': 2,
            'company': {
                'id': 20,
                'owner': {
                    'id': 200
                }
            }
        }, {
            'id': 3,
            'company': {
                'id': 10,
                'owner': {
                    'id': 100
                }
            }
        }]
    }
    assert execute(query) == expected_result
