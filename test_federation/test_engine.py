from collections import defaultdict
from typing import (
    TypedDict,
)
from unittest import TestCase

from federation.directive import KeyDirective
from federation.endpoint import denormalize_entities
from federation.engine import Engine
from federation.validate import validate
from hiku.executors.sync import SyncExecutor
from hiku.graph import (
    Root,
    Field,
    Link,
    Node,
    Graph,
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


class Kid(TypedDict):
    name: str
    parent_id: int


astronauts = {
    1: Astronaut(id=1, name='Max', age=20),
    2: Astronaut(id=2, name='Bob', age=25),
}

kids = {
    1: Kid(name='John', parent_id=1),
    2: Kid(name='Kirk', parent_id=1),
    3: Kid(name='Dom', parent_id=2),
}

planets = {
    'mars': Planet(name='mars', order=4),
    'earth': Planet(name='earth', order=3),
}


def astronaut_resolver(fields, ids):
    def _get_field(f, astronaut):
        return astronaut[f.name]

    for astro_id in ids:
        astronaut = astronauts.get(astro_id)
        yield [_get_field(f, astronaut) for f in fields]


def planet_resolver(fields, ids):
    def _get_field(f, planet):
        return planet[f.name]

    for name in ids:
        planet = planets.get(name)
        yield [_get_field(f, planet) for f in fields]


def kid_resolver(fields, ids):
    def _get_field(f, kid):
        return kid[f.name]

    for id_ in ids:
        kid = kids.get(id_)
        yield [_get_field(f, kid) for f in fields]


def link_kids(ids):
    kids_by_parent = defaultdict(list)
    for kid_id, kid in kids.items():
        kids_by_parent[kid['parent_id']].append(kid_id)

    res = []
    for parent_id in ids:
        res.append(kids_by_parent[parent_id])

    return res


def direct_link(ids):
    return ids


GRAPH = Graph([
    Node('Astronaut', [
        Field('id', Integer, astronaut_resolver),
        Field('name', String, astronaut_resolver),
        Field('age', Integer, astronaut_resolver),
        Link('kids', Sequence[TypeRef['Kid']], link_kids, requires='id')
    ], directives=[KeyDirective('id')]),
    Node('Kid', [
        Field('name', String, kid_resolver),
        Field('parent_id', Integer, kid_resolver),
    ]),
    Node('Planet', [
        Field('name', String, planet_resolver),
        Field('order', Integer, planet_resolver),
    ], directives=[KeyDirective('name')]),
    Root([
        Link(
            'astronauts',
            Sequence[TypeRef['Astronaut']],
            direct_link,
            requires=None,
            options=None,
        ),
    ]),
])


def execute(graph, query_, ctx=None):
    engine = Engine(SyncExecutor())
    return engine.execute(graph, query_, ctx=ctx)


class TestEngine(TestCase):
    def test_validate_entities_query(self):
        from hiku.query import Node, Field, Link

        query = Node(fields=[
            Link(
                '_entities',
                Node(fields=[
                    Field('name'),
                    Field('age'),
                    Link('kids', Node(fields=[
                        Field('name'),
                    ]))
                ]),
                options={
                    'representations': [
                        {'__typename': 'Astronaut', 'id': 1},
                        {'__typename': 'Astronaut', 'id': 2},
                    ]
                }
            )
        ])

        errors = validate(GRAPH, query)
        self.assertListEqual(errors, [])

    def test_execute_one_typename(self):
        from hiku.query import Node, Field, Link

        query = Node(fields=[
            Link(
                '_entities',
                Node(fields=[
                    Field('name'),
                    Field('age'),
                    Link('kids', Node(fields=[
                        Field('name'),
                    ]))
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
        data = denormalize_entities(
            GRAPH,
            query,
            result.data
        )

        expect = [{
            'name': 'Max',
            'age': 20,
            'id': 1,
            'kids': [{'name': 'John'}, {'name': 'Kirk'}]
        }, {
            'name': 'Bob',
            'age': 25,
            'id': 2,
            'kids': [{'name': 'Dom'}]
        }]
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
        data = denormalize_entities(
            GRAPH,
            query,
            result.data
        )

        expect = [
            {'name': 'Max'},  # astronaut id 1
            {'name': 'mars'}   # planet name mars
        ]
        self.assertListEqual(expect, data)
