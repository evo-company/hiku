import textwrap

from hiku.graph import (
    Node,
    Field,
    Link,
    Option,
    Root, Union,
)
from hiku.types import (
    Record,
    Integer,
    String,
    TypeRef,
    Optional,
)
from hiku.graph import apply

from hiku.federation.graph import FederatedNode, Graph
from hiku.federation.directive import (
    External,
    Key,
    Extends,
)
from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine
from hiku.federation.introspection import FederatedGraphQLIntrospection
from hiku.federation.sdl import print_sdl
from hiku.executors.sync import SyncExecutor
from tests.test_federation.utils import field_resolver, link_resolver


def execute(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


GRAPH = Graph([
    FederatedNode('Order', [
        Field('cartId', Integer, field_resolver, directives=[External()]),
        Link('cart', TypeRef['Cart'], link_resolver, requires='cartId')
    ], directives=[Key('cartId'), Extends()]),
    FederatedNode('Cart', [
        Field('id', Integer, field_resolver),
        Field('status', TypeRef['Status'], field_resolver),
    ], directives=[Key('id')]),
    FederatedNode('CartItem', [
        Field('id', Integer, field_resolver),
    ], directives=[Key('id', resolvable=False)]),
    Root([
        Link(
            'order',
            Optional[TypeRef['Order']],
            link_resolver,
            requires=None,
            options=[
                Option('id', Integer),
            ],
        ),
    ]),
], data_types={
    'Status': Record[{
        'id': Integer,
        'title': String,
    }],
}, unions=[Union('Bucket', ['Cart'])],)


expected = """
    type Status {
      id: Int!
      title: String!
    }
    
    input IOStatus {
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
    
    type CartItem @key(fields: "id") {
      id: Int!
    }

    extend type Query {
      order(id: Int!): Order
    }
    
    scalar Any

    scalar _FieldSet
    
    union Bucket = Cart
    
    union _Entity = Cart | CartItem | Order

    type _Service {
      sdl: String!
    }
"""


def test_print_graph_sdl():
    sdl = print_sdl(GRAPH, federation_version=1)
    assert sdl.strip() == textwrap.dedent(expected).strip()


def test_print_introspected_graph_sdl():
    INTROSPECTED_GRAPH = apply(GRAPH, [
        FederatedGraphQLIntrospection(GRAPH),
    ])

    sdl = print_sdl(INTROSPECTED_GRAPH, federation_version=1)

    assert sdl.strip() == textwrap.dedent(expected).strip()
