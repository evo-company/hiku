import textwrap

from hiku.directives import Location
from hiku.graph import (
    Graph,
    Node,
    Field,
    Link,
    Option,
    Root,
)
from hiku.types import (
    Boolean, Record,
    Integer,
    String,
    TypeRef,
    Optional,
)
from hiku.graph import apply

from hiku.federation.directive import (
    schema_directive,
    FederationSchemaDirective,
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


@schema_directive(
    name='custom',
    locations=[Location.OBJECT],
    compose=True,
    import_url="https://myspecs.dev/myCustomDirective/v1.0"
)
class Custom(FederationSchemaDirective):
    ...


def execute(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


SaveOrderResultNode = Node(
    "SaveOrderResult",
    [
        Field("status", Boolean, lambda: None),
    ],
)

GRAPH = Graph([
    SaveOrderResultNode,
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
                Option('id', Integer),
            ],
        ),
    ]),
], data_types={
    'Status': Record[{
        'id': Integer,
        'title': String,
    }],
}, directives=[Custom])


MUTATION_GRAPH = Graph(
    GRAPH.nodes
    + [
        Root([
            Link(
                "saveOrder",
                TypeRef["SaveOrderResult"],
                lambda: None,
                options=[
                    Option("id", Integer),
                ],
                requires=None,
            ),
        ])
    ]
)


expected_tmpl = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@key", "@external", "@extends", "@composeDirective"]) @link(url: "https://myspecs.dev/myCustomDirective/v1.0", import: ["@custom"]) @composeDirective(name: "@custom")

    directive @custom on OBJECT

    type Status {
      id: Int!
      title: String!
    }
    
    input IOStatus {
      id: Int!
      title: String!
    }
    
    type SaveOrderResult {
      status: Boolean!
    }

    extend type Order @key(fields: "cartId", resolvable: true) {
      cartId: Int! @external
      cart: Cart!
    }

    type Cart @key(fields: "id", resolvable: true) {
      id: Int!
      status: Status!
    }

    extend type Query {
      order(id: Int!): Order
    }
    %s
    scalar Any
    
    union _Entity = Cart | Order

    type _Service {
      sdl: String!
    }
"""

expected_with_mutation_tmpl = """
    extend type Mutation {
      saveOrder(id: Int!): SaveOrderResult!
    }
"""

expected = expected_tmpl % ""
expected_with_mutation = expected_tmpl % expected_with_mutation_tmpl


def test_print_graph_sdl():
    sdl = print_sdl(GRAPH)
    assert sdl.strip() == textwrap.dedent(expected).strip()


def test_print_graph_and_mutation_graph_sdl():
    sdl = print_sdl(GRAPH, MUTATION_GRAPH)
    assert sdl.strip() == textwrap.dedent(expected_with_mutation).strip()


def test_print_introspected_graph_sdl():
    INTROSPECTED_GRAPH = apply(GRAPH, [
        FederatedGraphQLIntrospection(GRAPH),
    ])

    sdl = print_sdl(INTROSPECTED_GRAPH)

    assert sdl.strip() == textwrap.dedent(expected).strip()
