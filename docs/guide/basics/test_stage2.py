# data

data = {
    'character': {
        1: dict(name='James T. Kirk', species='Human'),
        2: dict(name='Spock', species='Vulcan/Human'),
        3: dict(name='Leonard McCoy', species='Human'),
    },
}

# graph definition

from hiku.graph import Graph, Root, Field, Edge, Link, Many
from hiku.engine import Engine
from hiku.result import denormalize
from hiku.readers.simple import read
from hiku.executors.sync import SyncExecutor

def character_data(fields, ids):
    result = []
    for id_ in ids:
        character = data['character'][id_]
        result.append([character[field.name] for field in fields])
    return result

def to_characters_link():
    return [1, 2, 3]

GRAPH = Graph([
    Edge('character', [
        Field('name', character_data),
        Field('species', character_data),
    ]),
    Root([
        Link('characters', Many, to_characters_link,
             edge='character', requires=None),
    ]),
])

# test

hiku_engine = Engine(SyncExecutor())

def execute(graph, query_string):
    query = read(query_string)
    result = hiku_engine.execute(graph, query)
    return denormalize(graph, result, query)

def test():
    result = execute(GRAPH, '[{:characters [:name :species]}]')
    assert result == {
        "characters": [
            {
                "species": "Human",
                "name": "James T. Kirk",
            },
            {
                "species": "Vulcan/Human",
                "name": "Spock",
            },
            {
                "species": "Human",
                "name": "Leonard McCoy",
            },
        ],
    }
