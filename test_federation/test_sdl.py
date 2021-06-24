from unittest import TestCase

from federation.directive import (
    KeyDirective,
    ExternalDirective,
    ExtendsDirective,
)
from federation.endpoint import FederatedGraphQLEndpoint
from federation.engine import Engine
from federation.introspection import FederatedGraphQLIntrospection
from federation.sdl import print_sdl
from hiku.executors.sync import SyncExecutor
from hiku.graph import (
    Option,
    Root,
    Field,
    apply,
    Node,
    Link,
    Graph,
)
from hiku.types import (
    Integer,
    String,
    TypeRef,
    Sequence,
    Optional,
    Record,
)


def mock_link(): pass
def mock_resolver(): pass


def noop_resolver(ids):
    raise Exception(f'noop resolver entered with {ids}')


def cart_order_resolver(ids):
    raise Exception(f'cart->order resolver entered with {ids}')


data_types = {
    'Status': Record[{
        'id': Integer,
        'title': String,
    }],
}


GRAPH = Graph([
    Node('Order', [
        Field('cartId', Integer, noop_resolver,
              directives=[ExternalDirective()]),
        Field('cart', TypeRef['Cart'], cart_order_resolver),
    ], directives=[KeyDirective('cartId'), ExtendsDirective()]),
    Node('Cart', [
        Field('id', Integer, mock_resolver),
        Field('status', TypeRef['Status'], mock_resolver),
        Link('items', Sequence[TypeRef['CartItem']], mock_link,
             requires='id')
    ], directives=[KeyDirective('id')]),
    Node('CartItem', [
        Field('id', Integer, mock_resolver),
        Field('cart_id', Integer, mock_resolver),
        Field('name', String, mock_resolver),
        Field('photo', Optional[String], lambda: None, options=[
            Option('width', Integer),
            Option('height', Integer),
        ]),
    ]),
    Root([
        Link(
            'cart',
            Optional[TypeRef['Cart']],
            mock_link,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
], data_types=data_types)


INTROSPECTED_GRAPH = apply(GRAPH, [
    FederatedGraphQLIntrospection(GRAPH),
])


def execute(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


class TestSDL(TestCase):
    def test_print_graph_sdl(self):
        sdl = print_sdl(GRAPH)
        expected = [
            'scalar Any',
            '',
            'type Status {',
            '  id: Int!',
            '  title: String!',
            '}',
            '',
            'type Order @key(fields: "cartId") @extends {',
            '  cartId: Int! @external',
            '  cart: Cart!',
            '}',
            '',
            'type Cart @key(fields: "id") {',
            '  id: Int!',
            '  status: Status!',
            '  items: [CartItem!]!',
            '}',
            '',
            'type CartItem {',
            '  id: Int!',
            '  cart_id: Int!',
            '  name: String!',
            '  photo(width: Int!, height: Int!): String',
            '}',
            '',
            'extend type Query {',
            '  cart(id: Int!): Cart',
            '}'
        ]
        self.assertEqual(sdl.splitlines(), expected)

    def test_print_introspected_graph_sdl(self):
        sdl = print_sdl(INTROSPECTED_GRAPH)
        expected = [
            'scalar Any',
            '',
            'type Status {',
            '  id: Int!',
            '  title: String!',
            '}',
            '',
            'type Order @key(fields: "cartId") @extends {',
            '  cartId: Int! @external',
            '  cart: Cart!',
            '}',
            '',
            'type Cart @key(fields: "id") {',
            '  id: Int!',
            '  status: Status!',
            '  items: [CartItem!]!',
            '}',
            '',
            'type CartItem {',
            '  id: Int!',
            '  cart_id: Int!',
            '  name: String!',
            '  photo(width: Int!, height: Int!): String',
            '}',
            '',
            'extend type Query {',
            '  cart(id: Int!): Cart',
            '}'
        ]
        self.assertEqual(sdl.splitlines(), expected)
