from typing import TypedDict
from unittest import TestCase

from federation.entities import FederatedResolver
from federation.graph import (
    ExtendLink,
    FederatedGraph,
    ExtendNode,
)
from hiku.denormalize.graphql import DenormalizeGraphQL
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.graph import (
    Option,
    Root,
    Field,
)
from hiku.introspection.graphql import QUERY_ROOT_NAME
from hiku.readers.graphql import read
from hiku.types import (
    Integer,
    String,
    TypeRef,
    Sequence,
)

def mock_link(): pass
def direct_link(ids):
    return ids


class Astronaut(TypedDict):
    id: int
    name: str
    age: int


astronauts = {
    1: Astronaut(id=1, name='Max', age=20),
    2: Astronaut(id=2, name='Bob', age=25),
}


class AstronautResolver(FederatedResolver):
    def __call__(self, fields, ids):
        res = []

        for astro_id in ids:
            astronaut = astronauts.get(astro_id)
            res.append([self._get_field(f, astronaut) for f in fields])

        return res

    def _get_field(self, f: Field, astronaut: Astronaut):
        if f.name == 'id':
            return astronaut['id']
        if f.name == 'name':
            return astronaut['name']
        if f.name == 'age':
            return astronaut['age']

    def resolve_references(self, refs, fields):
        result = []
        for ref in refs:
            astronaut = astronauts.get(ref['id'])
            result.append({
                f.name: self._get_field(f, astronaut) for f in fields
            })

        return result


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

astronaut_resolver = AstronautResolver()

AstronautNode = ExtendNode('Astronaut', [
    Field('id', Integer, astronaut_resolver),
    Field('name', String, astronaut_resolver),
    Field('age', Integer, astronaut_resolver),
], keys=['id'])

GRAPH = FederatedGraph([
    AstronautNode,
    Root(ROOT_FIELDS),
])


hiku_engine = Engine(SyncExecutor())


def execute(graph, query_string, variables):
    query = read(query_string, variables)
    result = hiku_engine.execute(graph, query)
    return DenormalizeGraphQL(graph, result, QUERY_ROOT_NAME).process(query)


class TestEntities(TestCase):
    def test_resolve_entities(self):
        query = """
        query ($representations: [_Any!]!) {
          _entities(representations: $representations) {
            ... on Astronaut {
              name
              age
            }
          }
        }
        """
        result = execute(GRAPH, query, dict(representations=[
            {'__typename': 'Astronaut', 'id': 1},
            {'__typename': 'Astronaut', 'id': 2},
        ]))

        self.assertEqual(result, {'_entities': [
            {'age': 20, 'name': 'Max'},
            {'age': 25, 'name': 'Bob'},
        ]})

