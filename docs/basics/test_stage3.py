# data

data = {
    'Character': {
        1: dict(id=1, name='James T. Kirk', species='Human'),
        2: dict(id=2, name='Spock', species='Vulcan/Human'),
        3: dict(id=3, name='Leonard McCoy', species='Human'),
    },
    'Actor': {
        1: dict(id=1, character_id=1, name='William Shatner'),
        2: dict(id=2, character_id=2, name='Leonard Nimoy'),
        3: dict(id=3, character_id=3, name='DeForest Kelley'),
        4: dict(id=4, character_id=1, name='Chris Pine'),
        5: dict(id=5, character_id=2, name='Zachary Quinto'),
        6: dict(id=6, character_id=3, name='Karl Urban'),
    },
}

# graph definition

from collections import defaultdict

from hiku.graph import Graph, Root, Field, Node, Link
from hiku.types import TypeRef, Sequence

def character_data(fields, ids):
    result = []
    for id_ in ids:
        character = data['Character'][id_]
        result.append([character[field.name] for field in fields])
    return result

def actor_data(fields, ids):
    result = []
    for id_ in ids:
        actor = data['Actor'][id_]
        result.append([actor[field.name] for field in fields])
    return result

def character_to_actors_link(ids):
    mapping = defaultdict(list)
    for row in data['Actor'].values():
        mapping[row['character_id']].append(row['id'])
    return [mapping[id_] for id_ in ids]

def actor_to_character_link(ids):
    mapping = {}
    for row in data['Actor'].values():
        mapping[row['id']] = row['character_id']
    return [mapping[id_] for id_ in ids]

def to_characters_link():
    return [1, 2, 3]

GRAPH = Graph([
    Node('Character', [
        Field('id', None, character_data),
        Field('name', None, character_data),
        Field('species', None, character_data),
        Link('actors', Sequence[TypeRef['Actor']],
             character_to_actors_link, requires='id'),
    ]),
    Node('Actor', [
        Field('id', None, actor_data),
        Field('name', None, actor_data),
        Link('character', TypeRef['Character'],
             actor_to_character_link, requires='id'),
    ]),
    Root([
        Link('characters', Sequence[TypeRef['Character']],
             to_characters_link, requires=None),
    ]),
])

# test

from hiku.engine import Engine
from hiku.result import denormalize
from hiku.readers.graphql import read
from hiku.executors.sync import SyncExecutor

hiku_engine = Engine(SyncExecutor())

def execute(graph, query_string):
    query = read(query_string)
    result = hiku_engine.execute(graph, query)
    return denormalize(graph, result)

def test_link():
    result = execute(GRAPH, "{ characters { name actors { name } } }")
    assert result == {
        'characters': [
            {'name': 'James T. Kirk',
             'actors': [{'name': 'William Shatner'},
                        {'name': 'Chris Pine'}]},
            {'name': 'Spock',
             'actors': [{'name': 'Leonard Nimoy'},
                        {'name': 'Zachary Quinto'}]},
            {'name': 'Leonard McCoy',
             'actors': [{'name': 'DeForest Kelley'},
                        {'name': 'Karl Urban'}]},
        ],
    }

def test_link_cycle():
    result = execute(GRAPH, "{ characters { name actors { name character { name } } } }")
    assert result == {
        'characters': [
            {'name': 'James T. Kirk',
             'actors': [{'name': 'William Shatner',
                         'character': {'name': 'James T. Kirk'}},
                        {'name': 'Chris Pine',
                         'character': {'name': 'James T. Kirk'}}]},
            {'name': 'Spock',
             'actors': [{'name': 'Leonard Nimoy',
                         'character': {'name': 'Spock'}},
                        {'name': 'Zachary Quinto',
                         'character': {'name': 'Spock'}}]},
            {'name': 'Leonard McCoy',
             'actors': [{'name': 'DeForest Kelley',
                         'character': {'name': 'Leonard McCoy'}},
                        {'name': 'Karl Urban',
                         'character': {'name': 'Leonard McCoy'}}]},
        ],
    }
