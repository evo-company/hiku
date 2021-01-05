from unittest import TestCase
from federation.graph import (
    resolve_service,
    ExtendLink,
    FederatedGraph,
    ExtendNode,
)
from federation.sdl import print_sdl
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import (
    Option,
    Root,
    Field,
)
from hiku.readers.simple import read
from hiku.result import denormalize
from hiku.types import (
    Integer,
    String,
    TypeRef,
    Sequence,
)


def mock_link(): pass
def mock_resolver(): pass


AstronautLink = ExtendLink(
    'astronaut',
    TypeRef['Astronaut'],
    mock_link,
    requires=None,
    options=[
        Option('id', Integer)
    ],
)

AstronautsLink = ExtendLink(
    'astronauts',
    Sequence[TypeRef['Astronaut']],
    mock_link,
    requires=None,
    options=None,
)

ROOT_FIELDS = [
    AstronautLink,
    AstronautsLink,
]

AstronautNode = ExtendNode('Astronaut', [
    Field('id', Integer, mock_resolver),
    Field('name', String, mock_resolver),
    Field('age', Integer, mock_resolver),
], keys=['id'])

GRAPH = FederatedGraph([
    AstronautNode,
    Root(ROOT_FIELDS),
])


hiku_engine = Engine(SyncExecutor())


def execute(graph, query_string):
    query = read(query_string)
    result = hiku_engine.execute(graph, query)
    return denormalize(graph, result)


class TestSDL(TestCase):
    def test_resolve_sdl_correct(self):
        [service] = resolve_service(ROOT_FIELDS, [AstronautNode])
        expected = (
            'type Astronaut @key(fields: "id") {\n  '
            'id: Int!\n  '
            'name: String!\n  '
            'age: Int!\n}\n\n'
            'extend type Query { '
            'astronaut(id: Int): Astronaut!\n\n'
            'astronauts: [Astronaut!]!\n \n}'
        )
        self.assertEqual(service['sdl'], expected)

    def test_print_sdl_for_extended_link(self):
        sdl = print_sdl(AstronautLink)
        expected = 'astronaut(id: Int): Astronaut!\n'
        self.assertEqual(sdl, expected)

        sdl = print_sdl(AstronautsLink)
        expected = 'astronauts: [Astronaut!]!\n'
        self.assertEqual(sdl, expected)

    def test_print_sdl_for_extended_node(self):
        sdl = print_sdl(AstronautNode)
        exp = (
            'type Astronaut @key(fields: "id") '
            '{\n  id: Int!\n  name: String!\n  age: Int!\n}\n'
        )
        self.assertEqual(sdl, exp)

    def test_query_service_sdl(self):
        result = execute(GRAPH, '[{:_service [:sdl]}]')
        expected = (
            'type Astronaut @key(fields: \"id\") {\n  '
            'id: Int!\n  '
            'name: String!\n  '
            'age: Int!\n}\n\n'
            'extend type Query { '
            'astronaut(id: Int): Astronaut!\n\n'
            'astronauts: [Astronaut!]!\n \n}'
        )
        self.assertEqual(result, {'_service': {'sdl': expected}})
