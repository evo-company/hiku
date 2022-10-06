from hiku.directives import Deprecated
from hiku.federation.directive import (
    External,
    Key,
    Extends,
)
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
    Sequence,
    Optional,
)
from hiku.utils import listify


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


@listify
def cart_item_resolver(fields, ids):
    for item_id in ids:
        item = get_by_id(item_id, data['cart_items'])
        yield [item[f.name] for f in fields]


async def async_cart_item_resolver(fields, ids):
    return cart_item_resolver(fields, ids)


@listify
def link_cart_items(cart_ids):
    for cart_id in cart_ids:
        yield [item['id'] for item
               in find_all_by_id(cart_id, data['cart_items'], key='cart_id')]


async def async_link_cart_items(ids):
    return link_cart_items(ids)


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
        Field('cartId', Integer, ids_resolver,
              directives=[External()]),
        Link('oldCart', TypeRef['Cart'], direct_link, requires='cartId',
             directives=[Deprecated('use cart instead')]),
        Link('cart', TypeRef['Cart'], direct_link, requires='cartId'),
    ], directives=[Key('cartId'), Extends()]),
    Node('Cart', [
        Field('id', Integer, cart_resolver),
        Field('status', TypeRef['Status'], cart_resolver),
        Link('items', Sequence[TypeRef['CartItem']], link_cart_items,
             requires='id')
    ], directives=[Key('id')]),
    Node('CartItem', [
        Field('id', Integer, cart_item_resolver),
        Field('cart_id', Integer, cart_item_resolver),
        Field(
            'name',
            String,
            cart_item_resolver,
            directives=[Deprecated('do not use')]
        ),
        Field('photo', Optional[String], lambda: None, options=[
            Option('width', Integer),
            Option('height', Integer),
        ]),
    ]),
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


ASYNC_GRAPH = Graph([
    Node('Order', [
        Field('cartId', Integer, async_ids_resolver,
              directives=[External()]),
        Link('cart', TypeRef['Cart'], async_direct_link, requires='cartId'),
    ], directives=[Key('cartId'), Extends()]),
    Node('Cart', [
        Field('id', Integer, async_cart_resolver),
        Field('status', TypeRef['Status'], async_cart_resolver),
        Link('items', Sequence[TypeRef['CartItem']], async_link_cart_items,
             requires='id')
    ], directives=[Key('id')]),
    Node('CartItem', [
        Field('id', Integer, async_cart_item_resolver),
        Field('cart_id', Integer, async_cart_item_resolver),
        Field('name', String, async_cart_item_resolver),
        Field('photo', Optional[String], lambda: None, options=[
            Option('width', Integer),
            Option('height', Integer),
        ]),
    ]),
    Root([
        Link(
            'cart',
            Optional[TypeRef['Cart']],
            async_ids_resolver,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
], data_types=data_types)
