import textwrap
from typing import Any

from hiku.directives import Location
from hiku.enum import Enum
from hiku.graph import (
    Node,
    Field,
    Link,
    Option,
    Root,
    Union,
)
from hiku.types import (
    Boolean,
    EnumRef,
    Record,
    Integer,
    String,
    TypeRef,
    Optional,
    UnionRef,
)
from hiku.scalar import Scalar
from hiku.graph import apply

from hiku.federation.graph import FederatedNode, Graph
from hiku.federation.directive import (
    Override,
    schema_directive,
    FederationSchemaDirective,
    External,
    Key,
    Extends,
)
from hiku.federation.introspection import FederatedGraphQLIntrospection
from hiku.federation.sdl import print_sdl
from tests.test_federation.utils import field_resolver, link_resolver


@schema_directive(
    name='custom',
    locations=[Location.OBJECT],
    compose=True,
    import_url="https://myspecs.dev/myCustomDirective/v1.0"
)
class Custom(FederationSchemaDirective):
    ...


class Long(Scalar):
    @classmethod
    def parse(cls, value: Any) -> int:
        return int(value)

    @classmethod
    def serialize(cls, value: Any) -> int:
        return int(value)


SaveOrderResultNode = Node(
    "SaveOrderResult",
    [
        Field("status", Boolean, lambda: None),
    ],
)

GRAPH = Graph([
    SaveOrderResultNode,
    FederatedNode('Order', [
        Field('cartId', Integer, field_resolver, directives=[External()]),
        Link('cart', TypeRef['Cart'], link_resolver, requires='cartId')
    ], directives=[Key('cartId'), Extends()]),
    FederatedNode('Cart', [
        Field('id', Integer, field_resolver),
        Field('status', TypeRef['Status'], field_resolver, description="Cart status"),
        Field('_secret', String, field_resolver),
        Field('currency', EnumRef['Currency'], field_resolver),
    ], directives=[Key('id')]),
    FederatedNode('CartItem', [
        Field('id', Integer, field_resolver),
        Field('productId', Long, field_resolver),
        Field(
            'productName',
            String,
            field_resolver,
            directives=[Override("service2")]
        ),
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
        Link(
            'bucket',
            UnionRef['Bucket'],
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
}, directives=[Custom], unions=[
    Union('Bucket', ['Cart'])
], enums=[
    Enum('Currency', ['UAH', 'USD'])
], scalars=[Long])


MUTATION_GRAPH = Graph.from_graph(
    GRAPH,
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
)


expected_tmpl = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@key", "@external", "@extends", "@override", "@composeDirective"]) @link(url: "https://myspecs.dev/myCustomDirective/v1.0", import: ["@custom"]) @composeDirective(name: "@custom")

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
      "Cart status"
      status: Status!
      currency: Currency!
    }
    
    type CartItem @key(fields: "id", resolvable: false) {
      id: Int!
      productId: Long!
      productName: String! @override(from: "service2")
    }

    extend type Query {
      order(id: Int!): Order
      bucket(id: Int!): Bucket!
    }
    %s
    scalar Any

    scalar Long

    scalar _Any

    scalar _FieldSet

    scalar link__Import

    enum Currency {
      UAH
      USD
    }
    
    union Bucket = Cart
    
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
