import logging

from flask import Flask, request, jsonify

from hiku.federation.directive import Key
from hiku.federation.engine import Engine
from hiku.federation.graph import Graph, FederatedNode
from hiku.federation.schema import Schema
from hiku.graph import (
    Root,
    Field,
    Option,
    Link,
)
from hiku.types import (
    Integer,
    TypeRef,
    String,
    Optional,
    Sequence,
)
from hiku.executors.sync import SyncExecutor
from hiku.utils import listify


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


@listify
def cart_resolver(fields, ids):
    for cart_id in ids:
        cart = get_by_id(cart_id, data['carts'])
        yield [cart[f.name] for f in fields]


@listify
def cart_item_resolver(fields, ids):
    for item_id in ids:
        item = get_by_id(item_id, data['cart_items'])
        yield [item[f.name] for f in fields]


@listify
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


def resolve_cart_reference(representations):
    return [r['id'] for r in representations]


def resolve_cart_item_reference(representations):
    return [r['id'] for r in representations]


"""
Example of `cart` subgraph.

`cart` subgraph has `Cart` and `CartItem` types which can be referenced
from other subgraphs.
"""
QUERY_GRAPH = Graph([
    FederatedNode(
        'Cart',
        [
            Field('id', Integer, cart_resolver),
            Field('status', String, cart_resolver),
            Link('items', Sequence[TypeRef['CartItem']], link_cart_items,
                 requires='id')
        ],
        directives=[Key('id')],
        resolve_reference=resolve_cart_reference
    ),
    FederatedNode(
        'CartItem',
        [
            Field('id', Integer, cart_item_resolver),
            Field('cart_id', Integer, cart_item_resolver),
            Field('name', String, cart_item_resolver),
        ],
        directives=[Key('id')],
        resolve_reference=resolve_cart_item_reference
    ),
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

schema = Schema(
    Engine(SyncExecutor()),
    QUERY_GRAPH,
)


@app.route('/graphql', methods={'POST'})
def handle_graphql():
    data = request.get_json()
    result = schema.execute_sync(data)
    resp = jsonify(result)
    return resp


def main():
    logging.basicConfig(level=logging.DEBUG)

    app.run(host='0.0.0.0', port=4001, debug=True)


if __name__ == '__main__':
    """
    Run server: python3 ./examples/graphql_federation_v2.py
    """

    main()
