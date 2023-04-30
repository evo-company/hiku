import textwrap

from hiku.federation.v1.directive import Extends, External, Key
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

from hiku.federation.v1.endpoint import FederatedGraphQLEndpoint
from hiku.federation.v1.engine import Engine
from hiku.federation.v1.introspection import FederatedGraphQLIntrospection
from hiku.federation.v1.sdl import print_sdl
from hiku.executors.sync import SyncExecutor
from hiku.graph import apply
from tests.test_federation_v1.utils import field_resolver, link_resolver


def execute(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


GRAPH = Graph([
    Node('Order', [
        Field('cartId', Integer, field_resolver, directives=[External()]),
        Link('cart', TypeRef['Cart'], link_resolver, requires='cartId')
    ], directives=[Key('cartId'), Extends()]),
    Node('Cart', [
        Field('id', Integer, field_resolver),
        Field('status', TypeRef['Status'], field_resolver),
    ], directives=[Key('id')]),
    Root([
        Link(
            'order',
            Optional[TypeRef['Order']],
            link_resolver,
            requires=None,
            options=[
                Option('id', Integer)
            ],
        ),
    ]),
], data_types={
    'Status': Record[{
        'id': Integer,
        'title': String,
    }],
})


expected = """
    type Status {
      id: Int!
      title: String!
    }

    extend type Order @key(fields: "cartId") {
      cartId: Int! @external
      cart: Cart!
    }

    type Cart @key(fields: "id") {
      id: Int!
      status: Status!
    }

    extend type Query {
      order(id: Int!): Order
    }

    scalar Any

    union _Entity = Order | Cart
"""


def test_print_graph_sdl():
    sdl = print_sdl(GRAPH)
    assert sdl.strip() == textwrap.dedent(expected).strip()


def test_print_introspected_graph_sdl():
    INTROSPECTED_GRAPH = apply(GRAPH, [
        FederatedGraphQLIntrospection(GRAPH),
    ])

    sdl = print_sdl(INTROSPECTED_GRAPH)

    assert sdl.strip() == textwrap.dedent(expected).strip()
