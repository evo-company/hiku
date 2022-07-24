import logging

from flask import Flask, request, jsonify

from hiku.federation.directive import (
    Key,
    External,
    Extends,
)
from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine
from hiku.graph import (
    Root,
    Field,
    Option,
    Node,
    Link,
    Graph,
)
from hiku.types import (
    Integer,
    TypeRef,
    String,
    Optional,
    Sequence,
)
from hiku.executors.sync import SyncExecutor

log = logging.getLogger(__name__)


def get_by_id(id_, collection):
    for item in collection:
        if item['id'] == id_:
            return item


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


def cart_resolver(fields, ids):
    for cart_id in ids:
        cart = get_by_id(cart_id, data['carts'])
        yield [cart[f.name] for f in fields]


def cart_item_resolver(fields, ids):
    for item_id in ids:
        item = get_by_id(item_id, data['cart_items'])
        yield [item[f.name] for f in fields]


def link_cart_items(cart_ids):
    for cart_id in cart_ids:
        yield [item['id'] for item
               in find_all_by_id(cart_id, data['cart_items'], key='cart_id')]


def direct_link_id(opts):
    return opts['id']


def ids_resolver(fields, ids):
    return [[id_] for id_ in ids]


def direct_link(ids):
    return ids


QUERY_GRAPH = Graph([
    Node('Order', [
        Field('cartId', Integer, ids_resolver,
              directives=[External()]),
        Link('cart', TypeRef['Cart'], direct_link, requires='cartId'),
    ], directives=[Key('cartId'), Extends()]),
    Node('Cart', [
        Field('id', Integer, cart_resolver),
        Field('status', String, cart_resolver),
        Link('items', Sequence[TypeRef['CartItem']], link_cart_items,
             requires='id')
    ], directives=[Key('id')]),
    Node('CartItem', [
        Field('id', Integer, cart_item_resolver),
        Field('cart_id', Integer, cart_item_resolver),
        Field('name', String, cart_item_resolver),
        Field('photo', Optional[String], lambda: None, options=[
            Option('width', Integer),
            Option('height', Integer),
        ]),
    ]),
    Root([
        Link(
            'cart',
            Optional[TypeRef['Cart']],
            direct_link_id,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
])


app = Flask(__name__)

graphql_endpoint = FederatedGraphQLEndpoint(
    Engine(SyncExecutor()),
    QUERY_GRAPH,
)


@app.route('/graphql', methods={'POST'})
def handle_graphql():
    data = request.get_json()
    result = graphql_endpoint.dispatch(data)
    resp = jsonify(result)
    return resp


def main():
    logging.basicConfig()
    app.run(host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
