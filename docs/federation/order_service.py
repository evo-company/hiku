from flask import Flask, request, jsonify

from hiku.federation.graph import Graph, FederatedNode
from hiku.federation.schema import Schema
from hiku.federation.directive import Key

from hiku.graph import Root, Field, Link, Option
from hiku.types import ID, Integer, TypeRef, Optional
from hiku.executors.sync import SyncExecutor
from hiku.utils import to_immutable_dict

app = Flask(__name__)


def resolve_order_reference(representations):
    return [to_immutable_dict(r) for r in representations]


def order_fields_resolver(fields, representations):
    orders = []
    for rep in representations:
        if 'id' in rep:
            orders.append(get_order_by_id(rep['id']))
        elif 'cartId' in rep:
            orders.append(get_order_by_cart_id(rep['cartId']))

    def gen_fields(field, order):
        if field == 'id':
            return order.id
        elif field == 'status':
            return order.status
        elif field == 'cartId':
            return order.cart_id

    return [[gen_fields(f.name, o) for f in fields] for o in orders]


def direct_link(ids):
    return ids


QUERY_GRAPH = Graph([
    FederatedNode(
        'Order', [
            Field('id', ID, order_fields_resolver),
            Field('status', Integer, order_fields_resolver),
            Field('cartId', Integer, order_fields_resolver),
        ],
        directives=[Key('id'), Key('cartId')],
        resolve_reference=resolve_order_reference
    ),
    Root([
        Link(
            'order',
            Optional[TypeRef['Order']],
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
