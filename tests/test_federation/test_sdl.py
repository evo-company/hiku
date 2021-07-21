from unittest import TestCase

from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine
from hiku.federation.introspection import FederatedGraphQLIntrospection
from hiku.federation.sdl import print_sdl
from hiku.executors.sync import SyncExecutor
from hiku.graph import apply

from tests.test_federation.utils import GRAPH

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
