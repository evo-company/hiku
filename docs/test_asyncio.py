import uuid
import pytest
import asyncio

# setup storage

from sqlalchemy import MetaData, Table, Column
from sqlalchemy import Integer, String, ForeignKey, select
from sqlalchemy.sql.ddl import CreateTable

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

# setup test environment

import aiopg.sa

async def init_db(pg_dsn, *, loop):
    db_name = 'test_{}'.format(uuid.uuid4().hex)
    async with aiopg.sa.create_engine(pg_dsn, loop=loop) as db_engine:
        async with db_engine.acquire() as conn:
            await conn.execute('CREATE DATABASE {0}'.format(db_name))
            return db_name

async def setup_db(db_dsn, *, loop):
    async with aiopg.sa.create_engine(db_dsn, loop=loop) as db_engine:
        async with db_engine.acquire() as conn:
            await conn.execute(CreateTable(character_table))
            await conn.execute(CreateTable(actor_table))

            await conn.execute(character_table.insert().values([
                dict(id=1, name='James T. Kirk', species='Human'),
                dict(id=2, name='Spock', species='Vulcan/Human'),
                dict(id=3, name='Leonard McCoy', species='Human'),
            ]))
            await conn.execute(actor_table.insert().values([
                dict(id=1, character_id=1, name='William Shatner'),
                dict(id=2, character_id=2, name='Leonard Nimoy'),
                dict(id=3, character_id=3, name='DeForest Kelley'),
                dict(id=4, character_id=1, name='Chris Pine'),
                dict(id=5, character_id=2, name='Zachary Quinto'),
                dict(id=6, character_id=3, name='Karl Urban'),
            ]))

async def drop_db(pg_dsn, db_name, *, loop):
    async with aiopg.sa.create_engine(pg_dsn, loop=loop) as db_engine:
        async with db_engine.acquire() as conn:
            await conn.execute('DROP DATABASE {0}'.format(db_name))

@pytest.fixture(scope='session', name='db_dsn')
def db_dsn_fixture(request):
    loop = asyncio.get_event_loop()

    pg_dsn = 'postgresql://postgres:postgres@postgres:5432/postgres'
    db_name = loop.run_until_complete(init_db(pg_dsn, loop=loop))

    db_dsn = 'postgresql://postgres:postgres@postgres:5432/{}'.format(db_name)
    loop.run_until_complete(setup_db(db_dsn, loop=loop))

    def fin():
        loop.run_until_complete(drop_db(pg_dsn, db_name, loop=loop))

    request.addfinalizer(fin)
    return db_dsn

# define graph

from hiku.graph import Graph, Root, Node, Link, Field
from hiku.types import TypeRef, Sequence
from hiku.engine import pass_context
from hiku.sources.aiopg import FieldsQuery, LinkQuery

SA_ENGINE_KEY = 'sa-engine'

character_query = FieldsQuery(SA_ENGINE_KEY, character_table)

actor_query = FieldsQuery(SA_ENGINE_KEY, actor_table)

character_to_actors_query = LinkQuery(
    SA_ENGINE_KEY,
    from_column=actor_table.c.character_id,
    to_column=actor_table.c.id,
)

async def direct_link(ids):
    return ids

@pass_context
async def to_characters_query(ctx):
    query = select([character_table.c.id])
    async with ctx[SA_ENGINE_KEY].acquire() as conn:
        rows = await conn.execute(query)
    return [row.id for row in rows]

@pass_context
async def to_actors_query(ctx):
    query = select([actor_table.c.id])
    async with ctx[SA_ENGINE_KEY].acquire() as conn:
        rows = await conn.execute(query)
    return [row.id for row in rows]

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

import aiopg.sa

from hiku.engine import Engine
from hiku.result import denormalize
from hiku.readers.simple import read
from hiku.executors.asyncio import AsyncIOExecutor

async def execute(hiku_engine, sa_engine, graph, query_string):
    query = read(query_string)
    result = await hiku_engine.execute(graph, query, {SA_ENGINE_KEY: sa_engine})
    return denormalize(graph, result)

@pytest.mark.asyncio(forbid_global_loop=True)
async def test_character_to_actors(db_dsn, event_loop):
    hiku_engine = Engine(AsyncIOExecutor(event_loop))
    async with aiopg.sa.create_engine(db_dsn, loop=event_loop) as sa_engine:
        result = await execute(hiku_engine, sa_engine, GRAPH,
                               '[{:characters [:name {:actors [:name]}]}]')
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

@pytest.mark.asyncio(forbid_global_loop=True)
async def test_actor_to_character(db_dsn, event_loop):
    hiku_engine = Engine(AsyncIOExecutor(event_loop))
    async with aiopg.sa.create_engine(db_dsn, loop=event_loop) as sa_engine:
        result = await execute(hiku_engine, sa_engine, GRAPH,
                               '[{:actors [:name {:character [:name]}]}]')
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
