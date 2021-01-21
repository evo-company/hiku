from typing import TypedDict
from unittest import TestCase

from federation.endpoint import denormalize
from federation.engine import Engine
from federation.graph import (
    ExtendNode,
    FederatedGraph,
    ExtendLink,
)
from hiku.executors.sync import SyncExecutor
from hiku.graph import (
    Root,
    Option,
    Field,
)

from hiku.types import (
    Integer,
    String,
    TypeRef,
    Sequence,
)

class Astronaut(TypedDict):
    id: int
    name: str
    age: int


class Planet(TypedDict):
    name: str
    order: int


astronauts = {
    1: Astronaut(id=1, name='Max', age=20),
    2: Astronaut(id=2, name='Bob', age=25),
}

planets = {
    'mars': Planet(name='mars', order=4),
    'earth': Planet(name='earth', order=3),
}


def astronaut_resolver(fields, ids):
    def _get_field(f, astronaut):
        if f.name == 'id':
            return astronaut['id']
        if f.name == 'name':
            return astronaut['name']
        if f.name == 'age':
            return astronaut['age']

    res = []

    for astro_id in ids:
        astronaut = astronauts.get(astro_id)
        res.append([_get_field(f, astronaut) for f in fields])

    return res


def planet_resolver(fields, ids):
    def _get_field(f, planet):
        return planet[f.name]

    res = []

    for name in ids:
        planet = planets.get(name)
        res.append([_get_field(f, planet) for f in fields])

    return res


def mock_link(): pass


def direct_link(ids):
    return ids


AstronautNode = ExtendNode('Astronaut', [
    Field('id', Integer, astronaut_resolver),
    Field('name', String, astronaut_resolver),
    Field('age', Integer, astronaut_resolver),
], keys=['id'])

PlanetNode = ExtendNode('Planet', [
    Field('name', String, planet_resolver),
    Field('order', Integer, planet_resolver),
], keys=['name'])

AstronautsLink = ExtendLink(
    'astronauts',
    Sequence[TypeRef['Astronaut']],
    mock_link,
    requires=None,
    options=None,
)

ROOT_FIELDS = [
    AstronautsLink,
]

GRAPH = FederatedGraph([
    AstronautNode,
    PlanetNode,
    Root(ROOT_FIELDS),
])


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query_, ctx=ctx)


class TestEngine(TestCase):
    def test_execute_one_typename(self):
        from hiku.query import Node, Field, Link

        query = Node(fields=[
            Link(
                '_entities',
                Node(fields=[
                    Field('name'),
                    Field('age'),
                ]),
                options={
                    'representations': [
                        {'__typename': 'Astronaut', 'id': 1},
                        {'__typename': 'Astronaut', 'id': 2},
                    ]
                }
            )
        ])
        result = execute(GRAPH, query, {})
        data = denormalize(
            GRAPH,
            query,
            result
        )

        expect = [
            {'name': 'Max', 'age': 20},  # id 1
            {'name': 'Bob', 'age': 25}   # id 2
        ]
        self.assertListEqual(expect, data)

    def test_execute_multiple_typenames(self):
        from hiku.query import Node, Field, Link

        query = Node(fields=[
            Link(
                '_entities',
                Node(fields=[
                    Field('name'),
                ]),
                options={
                    'representations': [
                        {'__typename': 'Astronaut', 'id': 1},
                        {'__typename': 'Planet', 'name': 'mars'}
                    ]
                }
            )
        ])
        result = execute(GRAPH, query, {})
        data = denormalize(
            GRAPH,
            query,
            result
        )

        expect = [
            {'name': 'Max'},  # astronaut id 1
            {'name': 'mars'}   # planet name mars
        ]
        self.assertListEqual(expect, data)
