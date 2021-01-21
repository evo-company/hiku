from collections import defaultdict
from typing import TypedDict
from unittest import TestCase

from federation.endpoint import denormalize
from federation.graph import (
    ExtendNode,
    FederatedGraph,
    ExtendLink,
)
from hiku.graph import (
    Root,
    Option,
    Field,
)

from hiku.result import (
    Proxy,
    Index,
    ROOT,
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
    pass


def planet_resolver(fields, ids):
    pass


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


INDEX = Index()

INDEX['Astronaut'] = defaultdict(None, {
    1: {'name': 'Max', 'age': 20},
    2: {'name': 'Bob', 'age': 25}
})

INDEX['Planet'] = defaultdict(None, {
    'mars': {'order': 4},
})

INDEX.finish()


class TestDenormalize(TestCase):
    def test_denormalize_one_typename(self):
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
        result = Proxy(INDEX, ROOT, query)
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

    def test_denormalize_multiple_typenames(self):
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
                        {'__typename': 'Planet', 'name': 'mars'}
                    ]
                }
            )
        ])
        result = Proxy(INDEX, ROOT, query)
        data = denormalize(
            GRAPH,
            query,
            result
        )

        expect = [
            {'name': 'Max', 'age': 20},  # astronaut id 1
            {'order': 4}   # planet name mars
        ]
        self.assertListEqual(expect, data)
