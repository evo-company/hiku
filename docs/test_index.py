import hiku.readers.simple
import hiku.readers.graphql

from hiku.engine import Engine
from hiku.builder import build, Q
from hiku.executors.sync import SyncExecutor

from hiku.graph import Graph, Root, Field, Node, Link
from hiku.types import String, Sequence, TypeRef
from hiku.result import denormalize


CHARACTER_DATA = {
    '819e79e09f40': {
        'name': 'James T. Kirk',
        'species': 'Human'
    },
    '4266ffb4fbc3': {
        'name': 'Spock',
        'species': 'Vulcan/Human'
    },
    'a562fedf8804': {
        'name': 'Leonard McCoy',
        'species': 'Human'
    }
}


def character_loader(fields, ids):
    for ident in ids:
        yield [CHARACTER_DATA[ident][f.name] for f in fields]


def characters_link():
    return ['819e79e09f40', '4266ffb4fbc3', 'a562fedf8804']


GRAPH = Graph([
    Node('Character', [
        Field('name', String, character_loader),
        Field('species', String, character_loader),
    ]),
    Root([
        Link('characters', Sequence[TypeRef['Character']],
             characters_link, requires=None),
    ]),
])


def query_graphql():
    return hiku.readers.graphql.read("""
    {
      characters {
        name
        species
      }
    }
    """)


def query_simple():
    return hiku.readers.simple.read("""
    [{:characters [:name :species]}]
    """)


def query_python():
    query = build([
        Q.characters[
            Q.name,
            Q.species,
        ],
    ])
    return query


def test():
    for query in [query_graphql(), query_simple(), query_python()]:
        hiku_engine = Engine(SyncExecutor())
        result = hiku_engine.execute(GRAPH, query)
        result = denormalize(GRAPH, result)
        assert result == \
        {
            "characters": [
                {
                    "name": "James T. Kirk",
                    "species": "Human"
                },
                {
                    "name": "Spock",
                    "species": "Vulcan/Human"
                },
                {
                    "name": "Leonard McCoy",
                    "species": "Human"
                }
            ]
        }
