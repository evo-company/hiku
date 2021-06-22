from unittest import TestCase

from federation.directive import KeyDirective
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
)


def mock_link(): pass
def mock_resolver(): pass


AstronautLink = Link(
    'astronaut',
    TypeRef['Astronaut'],
    mock_link,
    requires=None,
    options=[
        Option('id', Optional[Integer])
    ],
)

AstronautsLink = Link(
    'astronauts',
    Sequence[TypeRef['Astronaut']],
    mock_link,
    requires=None,
    options=None,
)

AstronautNode = Node('Astronaut', [
    Field('id', Integer, mock_resolver),
    Field('name', String, mock_resolver),
    Field('age', Integer, mock_resolver),
], directives=[
    KeyDirective('id')
])

ROOT_FIELDS = [
    AstronautLink,
    AstronautsLink,
]

GRAPH = Graph([
    AstronautNode,
    Root(ROOT_FIELDS),
])

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
        sdlected = print_sdl(GRAPH)
        expected = [
            'type Astronaut @key(fields: "id") {',
            '  id: Int!',
            '  name: String!',
            '  age: Int!', '}',
            '',
            'extend type Query {',
            '  astronaut(id: Int): Astronaut!',
            '  astronauts: [Astronaut!]!',
            '}'
        ]
        self.assertEqual(sdlected.splitlines(), expected)

    def test_print_introspected_graph_sdl(self):
        sdlected = print_sdl(INTROSPECTED_GRAPH)
        expected = [
            'type Astronaut @key(fields: "id") {',
            '  id: Int!',
            '  name: String!',
            '  age: Int!', '}',
            '',
            'extend type Query {',
            '  astronaut(id: Int): Astronaut!',
            '  astronauts: [Astronaut!]!',
            '}'
        ]
        self.assertEqual(sdlected.splitlines(), expected)
