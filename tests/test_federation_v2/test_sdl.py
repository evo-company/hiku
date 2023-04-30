import textwrap

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
from hiku.graph import apply

from hiku.federation.v2.directive import (
    External,
    Key,
    Extends,
)
from hiku.federation.v2.endpoint import FederatedGraphQLEndpoint
from hiku.federation.v2.engine import Engine
from hiku.federation.v2.introspection import FederatedGraphQLIntrospection
from hiku.federation.v2.sdl import print_sdl
from hiku.executors.sync import SyncExecutor
from tests.test_federation_v2.utils import field_resolver, link_resolver


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

    type _Service {
      sdl: String!
    }
"""

"""
      _entities(representations: [_Any!]!): [_Entity]!
      _service: _Service!
      
    scalar FieldSet
    scalar link__Import
    enum link__Purpose {
      SECURITY
      EXECUTION
    }
"""

# TODO: probably do not need extend type Query in 2 version
# TODO: do we need to print all directives ?
# https://www.apollographql.com/docs/federation/subgraph-spec/#subgraph-schema-additions

# TODO: do not add type into _entities if it is @key but resolvable=False
# https://www.apollographql.com/docs/federation/subgraph-spec/#example


def test_print_graph_sdl():
    sdl = print_sdl(GRAPH)
    assert sdl.strip() == textwrap.dedent(expected).strip()


def test_print_introspected_graph_sdl():
    INTROSPECTED_GRAPH = apply(GRAPH, [
        FederatedGraphQLIntrospection(GRAPH),
    ])

    sdl = print_sdl(INTROSPECTED_GRAPH)

    assert sdl.strip() == textwrap.dedent(expected).strip()
