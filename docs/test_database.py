# setup storage

from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, String, ForeignKey, select

metadata = MetaData()

character_table = Table(
    'character',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('species', String),
)

actor_table = Table(
    'actor',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('character_id', ForeignKey('character.id'), nullable=False),
)

sa_engine = create_engine('sqlite://')
metadata.create_all(sa_engine)

sa_engine.execute(character_table.insert().values([
    dict(id=1, name='James T. Kirk', species='Human'),
    dict(id=2, name='Spock', species='Vulcan/Human'),
    dict(id=3, name='Leonard McCoy', species='Human'),
]))
sa_engine.execute(actor_table.insert().values([
    dict(id=1, character_id=1, name='William Shatner'),
    dict(id=2, character_id=2, name='Leonard Nimoy'),
    dict(id=3, character_id=3, name='DeForest Kelley'),
    dict(id=4, character_id=1, name='Chris Pine'),
    dict(id=5, character_id=2, name='Zachary Quinto'),
    dict(id=6, character_id=3, name='Karl Urban'),
]))

# define graph

from hiku.graph import Graph, Root, Node, Link, Field
from hiku.types import TypeRef, Sequence
from hiku.engine import pass_context
from hiku.sources.sqlalchemy import FieldsQuery, LinkQuery

SA_ENGINE_KEY = 'sa-engine'

character_query = FieldsQuery(SA_ENGINE_KEY, character_table)

actor_query = FieldsQuery(SA_ENGINE_KEY, actor_table)

character_to_actors_query = LinkQuery(
    SA_ENGINE_KEY,
    from_column=actor_table.c.character_id,
    to_column=actor_table.c.id,
)

def direct_link(ids):
    return ids

@pass_context
def to_characters_query(ctx):
    query = select([character_table.c.id])
    return [row.id for row in ctx[SA_ENGINE_KEY].execute(query)]

@pass_context
def to_actors_query(ctx):
    query = select([actor_table.c.id])
    return [row.id for row in ctx[SA_ENGINE_KEY].execute(query)]

GRAPH = Graph([
    Node('Character', [
        Field('id', None, character_query),
        Field('name', None, character_query),
        Field('species', None, character_query),
        Link('actors', Sequence[TypeRef['Actor']], character_to_actors_query,
             requires='id'),
    ]),
    Node('Actor', [
        Field('id', None, actor_query),
        Field('name', None, actor_query),
        Field('character_id', None, actor_query),
        Link('character', TypeRef['Character'],
             direct_link, requires='character_id'),
    ]),
    Root([
        Link('characters', Sequence[TypeRef['Character']],
             to_characters_query, requires=None),
        Link('actors', Sequence[TypeRef['Actor']],
             to_actors_query, requires=None),
    ]),
])

# test graph

from hiku.engine import Engine
from hiku.result import denormalize
from hiku.readers.simple import read
from hiku.executors.sync import SyncExecutor

hiku_engine = Engine(SyncExecutor())


def execute(graph, query_string):
    query = read(query_string)
    result = hiku_engine.execute(graph, query, {SA_ENGINE_KEY: sa_engine})
    return denormalize(graph, result)


def test_character_to_actors():
    result = execute(GRAPH, '[{:characters [:name {:actors [:name]}]}]')
    assert result == {
        'characters': [
            {
                'name': 'James T. Kirk',
                'actors': [
                    {'name': 'William Shatner'},
                    {'name': 'Chris Pine'},
                ],
            },
            {
                'name': 'Spock',
                'actors': [
                    {'name': 'Leonard Nimoy'},
                    {'name': 'Zachary Quinto'},
                ],
            },
            {
                'name': 'Leonard McCoy',
                'actors': [
                    {'name': 'DeForest Kelley'},
                    {'name': 'Karl Urban'},
                ],
            },
        ],
    }

def test_actor_to_character():
    result = execute(GRAPH, '[{:actors [:name {:character [:name]}]}]')
    assert result == {
        'actors': [
            {
                'name': 'William Shatner',
                'character': {'name': 'James T. Kirk'},
            },
            {
                'name': 'Leonard Nimoy',
                'character': {'name': 'Spock'},
            },
            {
                'name': 'DeForest Kelley',
                'character': {'name': 'Leonard McCoy'},
            },
            {
                'name': 'Chris Pine',
                'character': {'name': 'James T. Kirk'},
            },
            {
                'name': 'Zachary Quinto',
                'character': {'name': 'Spock'},
            },
            {
                'name': 'Karl Urban',
                'character': {'name': 'Leonard McCoy'},
            },
        ],
    }
