# setup storage

from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, Unicode, ForeignKey, select

metadata = MetaData()

image_table = Table(
    'image',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', Unicode, nullable=False),
)

character_table = Table(
    'character',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('image_id', ForeignKey('image.id')),
    Column('name', Unicode),
)

sa_engine = create_engine('sqlite://')
metadata.create_all(sa_engine)

sa_engine.execute(image_table.insert().values([
    dict(id=1, name='j.kirk.jpg'),
    dict(id=2, name='spock.jpg'),
    dict(id=3, name='l.mccoy.jpg'),
]))
sa_engine.execute(character_table.insert().values([
    dict(id=1, image_id=1, name='James T. Kirk'),
    dict(id=2, image_id=2, name='Spock'),
    dict(id=3, image_id=3, name='Leonard McCoy'),
]))

# define low-level graph

from hiku.graph import Graph, Root, Node, Field, Link
from hiku.types import TypeRef, Sequence, Optional
from hiku.engine import pass_context, Nothing
from hiku.sources.sqlalchemy import FieldsQuery

SA_ENGINE_KEY = 'sa-engine'

image_query = FieldsQuery(SA_ENGINE_KEY, image_table)

character_query = FieldsQuery(SA_ENGINE_KEY, character_table)

def direct_link(ids):
    return ids

def maybe_direct_link(ids):
    return [id_ if id_ is not None else Nothing
            for id_ in ids]

@pass_context
def to_characters_query(ctx):
    query = select([character_table.c.id])
    return [row.id for row in ctx[SA_ENGINE_KEY].execute(query)]

_GRAPH = Graph([
    Node('Image', [
        Field('id', None, image_query),
        Field('name', None, image_query),
    ]),
    Node('Character', [
        Field('id', None, character_query),
        Field('image_id', None, character_query),
        Field('name', None, character_query),
        Link('image', Optional[TypeRef['Image']],
             maybe_direct_link, requires='image_id'),
    ]),
    Root([
        Link('characters', Sequence[TypeRef['Character']],
             to_characters_query, requires=None),
    ]),
])

# test low-level graph

from hiku.engine import Engine
from hiku.result import denormalize
from hiku.readers.simple import read
from hiku.executors.sync import SyncExecutor

hiku_engine = Engine(SyncExecutor())


def execute(graph, query_string):
    query = read(query_string)
    result = hiku_engine.execute(query, graph, ctx={SA_ENGINE_KEY: sa_engine})
    return denormalize(graph, result)


def test_low_level():
    result = execute(_GRAPH, '[{:characters [:name {:image [:id :name]}]}]')
    assert result == {
        'characters': [
            {'name': 'James T. Kirk',
             'image': {'id': 1, 'name': 'j.kirk.jpg'}},
            {'name': 'Spock',
             'image': {'id': 2, 'name': 'spock.jpg'}},
            {'name': 'Leonard McCoy',
             'image': {'id': 3, 'name': 'l.mccoy.jpg'}},
        ],
    }

# define high-level graph

from hiku.types import Record, Integer, String
from hiku.expr.core import S, define, if_some
from hiku.sources.graph import SubGraph

@define(Record[{'id': Integer, 'name': String}])
def image_url(image):
    return 'http://example.com/{id}-{name}'.format(id=image['id'],
                                                   name=image['name'])

character_sg = SubGraph(_GRAPH, 'Character')

GRAPH = Graph([
    Node('Character', [
        Field('id', None, character_sg),
        Field('name', None, character_sg),
        Field('image-url', None, character_sg.c(
            if_some([S.img, S.this.image],
                    image_url(S.img),
                    'http://example.com/no-photo.jpg'),
        )),
    ]),
    Root([
        Link('characters', Sequence[TypeRef['Character']],
             to_characters_query, requires=None),
    ]),
])

# test high-level graph

def test_high_level():
    result = execute(GRAPH, '[{:characters [:name :image-url]}]')
    assert result == {
        'characters': [
            {'name': 'James T. Kirk',
             'image-url': 'http://example.com/1-j.kirk.jpg'},
            {'name': 'Spock',
             'image-url': 'http://example.com/2-spock.jpg'},
            {'name': 'Leonard McCoy',
             'image-url': 'http://example.com/3-l.mccoy.jpg'},
        ],
    }
