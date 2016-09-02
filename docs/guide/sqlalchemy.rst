SQLAlchemy support
==================

Hiku provides support for loading data from SQL databases using SQLAlchemy_
library, but Hiku doesn't requires to use it's ORM layer, it requires only Core
SQLAlchemy_ functionality - tables definition and expression language to
construct SELECT queries.

Database schema
~~~~~~~~~~~~~~~

We will translate our previous example from the :doc:`introduction`, here is it's
database schema:

.. code-block:: python

    from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey

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

And let's store the same :ref:`data <introduction-data>` in our database:

.. code-block:: python

    from sqlalchemy import create_engine

    engine = create_engine('sqlite://')
    metadata.create_all(engine)

    for character_data in data['character'].values():
        engine.execute(character_table.insert().values(character_data))
    for actor_data in data['actor'].values():
        engine.execute(actor_table.insert().values(actor_data))

Then we will be able to expose these tables in our graph:

.. code-block:: python

    from hiku.graph import Graph, Root, Edge, Link, One, Many
    from hiku.engine import pass_context
    from hiku.sources import sqlalchemy as sa

    SA_ENGINE = 'sa-engine'  # 1

    character_query = sa.FieldsQuery(SA_ENGINE, character_table)  # 2

    actor_query = sa.FieldsQuery(SA_ENGINE, actor_table)

    to_actors_query = sa.LinkQuery(Many, SA_ENGINE, edge='actor',  # 3
                                   from_column=actor_table.c.character_id,
                                   to_column=actor_table.c.id)

    def to_character_func(ids):  # 4
        return ids

    @pass_context  # 5
    def to_characters_query(ctx):  # 6
        query = character_table.select(character_table.c.id)
        return [row.id for row in ctx[SA_ENGINE].execute(query)]  # 7

    GRAPH = Graph([
        Edge('character', [
            sa.Field('id', character_query),
            sa.Field('name', character_query),
            sa.Field('species', character_query),
            sa.Link('actors', to_actors_query, requires='id'),
        ]),
        Edge('actor', [
            sa.Field('id', actor_query),
            sa.Field('name', actor_query),
            sa.Field('character_id', actor_query),
            Link('character', One, to_character_func,  # 8
                 edge='character', requires='character_id'),
        ]),
        Root([
            Link('characters', Many, to_characters_query,  # 9
                 edge='character', requires=None),
        ]),
    ])

In the previous examples all the data was available as data structures, so no
special access method was required. With databases we will require a database
connection in order to fetch any data from it. Hiku provides simple and
implicit way to solve this issue without using global variables (thread-locals)
- by providing query execution context.

Query execution context is a simple mapping, where you can store and read values
during query execution. In this example we are using ``SA_ENGINE``
constant :sup:`[1]` as a key to access our SQLAlchemy's engine. In order to
access query context :py:func:`~hiku.engine.pass_context` decorator should
be used :sup:`[5]` and then ``to_characters_query`` function :sup:`[6]` will
receive it as a first positional argument. ``SA_ENGINE`` constant is used to get
SQLAlchemy's engine from the context :sup:`[7]` in order to execute SQL query.

:py:class:`~hiku.sources.sqlalchemy.FieldsQuery` :sup:`[2]` and
:py:class:`~hiku.sources.sqlalchemy.LinkQuery` :sup:`[3]` are using context
in the same manner.

Hiku's SQLAlchemy support is provided by
:py:class:`hiku.sources.sqlalchemy.FieldsQuery` and
:py:class:`hiku.sources.sqlalchemy.Field` to express table columns as fields in
the edge. And by :py:class:`hiku.sources.sqlalchemy.LinkQuery` and
:py:class:`hiku.sources.sqlalchemy.Link` to express relations between tables as
links between edges.

``to_character_func`` :sup:`[4]` is a special case: when one table contains
foreign key to the other table - `many-to-one` relation or `one-to-one`
relation, no additional queries needed to make a direct link between those
tables as edges. ``character`` link :sup:`[8]` is a good example of such direct
link.

Other relation types require to make additional query in order to fetch
linked edge ids. ``to_actors_query`` :sup:`[3]` for example. Such queries require
selecting only one table, ``actor_table`` in this example. SQL query will be
looking like this:

.. code-block:: sql

    SELECT actor.id from actor WHERE actor.character_id IN $character_ids;

List of ``$character_ids`` we already know (it is an ``id`` field of the current
edge), all we need is to fetch ``actor.id`` column to make a link from
``character`` edge to the ``actor`` edge.
:py:class:`~hiku.sources.sqlalchemy.LinkQuery` does this for you.

Query:

.. code-block:: python

    from pprint import pprint
    from hiku.engine import Engine
    from hiku.result import denormalize
    from hiku.readers.simple import read
    from hiku.executors.sync import SyncExecutor

    engine = Engine(SyncExecutor())

    query = read('[{:characters [:name {:actors [:name {:character [:name]}]}]}]')
    result = engine.execute(GRAPH, query, ctx={SA_ENGINE: sa_engine})

Result:

.. code-block:: python

    >>> pprint(denormalize(GRAPH, result, query))
    {'characters': [{'actors': [{'character': {'name': 'James T. Kirk'},
                                 'name': 'William Shatner'},
                                {'character': {'name': 'James T. Kirk'},
                                 'name': 'Chris Pine'}],
                     'name': 'James T. Kirk'},
                    {'actors': [{'character': {'name': 'Spock'},
                                 'name': 'Leonard Nimoy'},
                                {'character': {'name': 'Spock'},
                                 'name': 'Zachary Quinto'}],
                     'name': 'Spock'},
                    {'actors': [{'character': {'name': 'Leonard McCoy'},
                                 'name': 'DeForest Kelley'},
                                {'character': {'name': 'Leonard McCoy'},
                                 'name': 'Karl Urban'}],
                     'name': 'Leonard McCoy'}]}

.. _SQLAlchemy: http://www.sqlalchemy.org
