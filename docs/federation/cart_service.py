from flask import Flask, request, jsonify

from hiku.federation.graph import Graph, FederatedNode
from hiku.federation.schema import Schema
from hiku.federation.directive import Key

from hiku.graph import Root, Node, Field, Link, Option
from hiku.types import ID, Integer, Sequence, String, TypeRef, Optional
from hiku.executors.sync import SyncExecutor
from hiku.utils import to_immutable_dict

app = Flask(__name__)


def resolve_reference_by(key):
    def resolver(representations):
        return [r[key] for r in representations]

    return resolver


def cart_fields_resolver(fields, cart_ids):
    carts = get_carts_by_ids(cart_ids)

    def gen_fields(field, cart):
        if field == 'id':
            return cart.id

    return [[gen_fields(f.name, c) for f in fields] for c in carts]


def link_cart_items(cart_ids):
    return [get_cart_items_ids(cart_id) for cart_id in cart_ids]


def cart_item_fields_resolver(fields, cart_item_ids):
    items = get_cart_items_by_ids(cart_item_ids)

    def gen_fields(field, item):
        if field == 'id':
            return item.id
        elif field == 'productName':
            return item.product_name
        elif field == 'price':
            return item.price
        elif field == 'quantity':
            return item.quantity

    return [[gen_fields(f.name, i) for f in fields] for i in items]


def order_fields_resolver(fields, cart_ids):
    def gen_fields(field, cart_id):
        if field == 'cartId':
            return cart_id

    return [[gen_fields(f.name, cid) for f in fields] for cid in cart_ids]


def direct_link(ids):
    return ids


QUERY_GRAPH = Graph([
    Node('ShoppingCart', [
        Field('id', ID, cart_fields_resolver),
        Link(
            'items',
            Sequence[TypeRef['ShoppingCartItem']],
            link_cart_items,
            requires='id'
        ),
    ]),
    Node('ShoppingCartItem', [
        Field('id', ID, cart_item_fields_resolver),
        Field('productName', String, cart_item_fields_resolver),
        Field('price', Integer, cart_item_fields_resolver),
        Field('quantity', Integer, cart_item_fields_resolver),
    ]),
    FederatedNode(
        'Order', [
            Field('cartId', ID, order_fields_resolver),
            Link(
                'cart',
                TypeRef['ShoppingCart'],
                direct_link,
                requires='cartId'
            ),
            ],
        directives=[Key('cartId')],
        resolve_reference=resolve_reference_by("cartId")
    ),
    Root([
        Link(
            'cart',
            Optional[TypeRef['ShoppingCart']],
            direct_link,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
])

schema = Schema(SyncExecutor(), QUERY_GRAPH)

@app.route('/graphql', methods={'POST'})
def handle_graphql():
    data = request.get_json()
    result = schema.execute_sync(data)
    resp = jsonify({"data": result.data})
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4001)
