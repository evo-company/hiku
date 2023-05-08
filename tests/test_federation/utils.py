from hiku.graph import (
    Graph,
    Node,
    Field,
    Link,
    Option,
    Root,
)
from hiku.types import (
    Record,
    Integer,
    String,
    TypeRef,
    Optional,
)
from hiku.utils import listify
from hiku.federation.directive import (
    External,
    Key,
    Extends,
)


def get_by_id(id_, collection):
    for item in collection:
        if item['id'] == id_:
            return item


@listify
def find_all_by_id(id_, collection, key='id'):
    for item in collection:
        if item[key] == id_:
            yield item


data = {
    'carts': [
        dict(id=1, status='NEW'),
        dict(id=2, status='ORDERED'),
    ],
    'cart_items': [
        dict(id=10, cart_id=1, name='Ipad'),
        dict(id=20, cart_id=2, name='Book'),
        dict(id=21, cart_id=2, name='Pen'),
    ]
}


@listify
def cart_resolver(fields, ids):
    for cart_id in ids:
        cart = get_by_id(cart_id, data['carts'])
        yield [cart[f.name] for f in fields]


async def async_cart_resolver(fields, ids):
    return cart_resolver(fields, ids)


def direct_link_id(opts):
    return opts['id']


def ids_resolver(fields, ids):
    return [[id_] for id_ in ids]


async def async_ids_resolver(fields, ids):
    return [[id_] for id_ in ids]


def direct_link(ids):
    return ids


async def async_direct_link(ids):
    return ids


data_types = {
    'Status': Record[{
        'id': Integer,
        'title': String,
    }],
}

GRAPH = Graph([
    Node('Order', [
        Field('cartId', Integer, ids_resolver, directives=[External()]),
        Link('cart', TypeRef['Cart'], direct_link, requires='cartId'),
    ], directives=[
        Key("cartId"),
        Extends()
    ]),
    Node('Cart', [
        Field('id', Integer, cart_resolver),
        Field('status', TypeRef['Status'], cart_resolver),
    ], directives=[Key('id')]),
    Root([
        Link(
            'order',
            Optional[TypeRef['Order']],
            ids_resolver,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
], data_types=data_types)


ASYNC_GRAPH = Graph([
    Node('Order', [
        Field('cartId', Integer, async_ids_resolver,
              directives=[External()]),
        Link('cart', TypeRef['Cart'], async_direct_link, requires='cartId'),
    ], directives=[Key('cartId'), Extends()]),
    Node('Cart', [
        Field('id', Integer, async_cart_resolver),
        Field('status', TypeRef['Status'], async_cart_resolver),
    ], directives=[Key('id')]),
    Root([
        Link(
            'order',
            Optional[TypeRef['Order']],
            async_ids_resolver,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
], data_types=data_types)


def field_resolver(fields, ids):
    ...


def link_resolver(ids):
    ...
