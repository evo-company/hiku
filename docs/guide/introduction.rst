Introduction
============

Prerequisites
~~~~~~~~~~~~~

Here we will try to describe our first graph. To begin with we
will need to setup an environment:

.. code-block:: shell

  $ pip install hiku

And let's create a Python module for our playground (for example `sandbox.py`):

.. code-block:: python

  from typing import List, Any
  from datetime import datetime
  from collections import defaultdict

  from hiku.graph import Graph, Root, Edge, Field, Link, One, Many
  from hiku.engine import Engine
  from hiku.executors.sync import SyncExecutor

  engine = Engine(SyncExecutor())

  graph = Graph([
      Root([
          Field('datetime', lambda _: [datetime.now().isoformat()]),
      ]),
  ])

  if __name__ == '__main__':
      from wsgiref.simple_server import make_server
      from hiku.console.ui import ConsoleApplication
      app = ConsoleApplication(graph, engine, debug=True)
      http_server = make_server('localhost', 5000, app)
      http_server.serve_forever()

This is the simplest :py:class:`~hiku.graph.Graph` with only one
:py:class:`~hiku.graph.Field` in the :py:class:`~hiku.graph.Root` edge. You can
try to query this field using special web console, which will start when
we will try to run our module:

.. code-block:: shell

  $ python sandbox.py

Just open http://localhost:5000/ in your browser and make first query:

.. code-block:: clojure

  [:datetime]

You should get this result:

.. code-block:: javascript

  {
    "datetime": "2015-10-21T07:28:00.000000"
  }

In the reference documentation you can learn about
:py:class:`~hiku.graph.Field` class and it's arguments. As you can see, we
are using lambda-function as ``func`` argument and ignoring first positional
argument. This argument is a ``fields`` argument of type
``Sequence[hiku.query.Field]``. It is ignored because this function
is used only to resolve one fields value.

Introducing Edge and Link
~~~~~~~~~~~~~~~~~~~~~~~~~

This is cool, but what if we want to return some application data?
First of all lets define our data:

.. code-block:: python

  data = {
      'character': {
          1: dict(name='James T. Kirk', species='Human'),
          2: dict(name='Spock', species='Vulcan/Human'),
          3: dict(name='Leonard McCoy', species='Human'),
      },
  }

.. note:: For simplicity we will use in-memory data structures to store our data.
  How to load data from more sophisticated sources like databases will be
  explained in the next chapters.

Then lets extend our graph with one :py:class:`~hiku.graph.Edge` and one
:py:class:`~hiku.graph.Link`:

.. code-block:: python

  def get_character_data(fields: List[hiku.query.Field], ids: List[int]) \
          -> List[List[Any]]:
      result = []
      for id_ in ids:
          character = data['character'][id_]
          result.append([character[field.name] for field in fields])
      return result

  graph = Graph([
      Edge('character', [
          Field('name', get_character_data),
          Field('species', get_character_data),
      ]),
      Root([
          Field('datetime', lambda _: [datetime.now().isoformat()]),
          Link('characters', Many, lambda: [1, 2, 3],
               edge='character', requires=None),
      ]),
  ])

Then you will be able to try this query in the console:

.. code-block:: clojure

  [{:characters [:name :species]}]

And get this result:

.. code-block:: javascript

  {
    "characters": [
      {
        "species": "Human",
        "name": "James T. Kirk"
      },
      {
        "species": "Vulcan/Human",
        "name": "Spock"
      },
      {
        "species": "Human",
        "name": "Leonard McCoy"
      }
    ]
  }

``get_character_data`` function is used to resolve values for two
fields in the ``character`` edge. As you can see
it returns basically a list of lists with values in the same order as
it was requested in arguments (order of ids and fields should be
preserved).

This gives us ability to resolve some fields simultaneously for
different objects in just one simple function when this is possible and
will improve performance (to eliminate N+1 problem and load related
data together).

Linking Edge to Edge
~~~~~~~~~~~~~~~~~~~~

Let's extend our data with one more entity - ``actor``:

.. _introduction-data:

.. code-block:: python

  data = {
      'character': {
          1: dict(id=1, name='James T. Kirk', species='Human'),
          2: dict(id=2, name='Spock', species='Vulcan/Human'),
          3: dict(id=3, name='Leonard McCoy', species='Human'),
      },
      'actor': {
          1: dict(id=1, character_id=1, name='William Shatner'),
          2: dict(id=2, character_id=2, name='Leonard Nimoy'),
          3: dict(id=3, character_id=3, name='DeForest Kelley'),
          4: dict(id=4, character_id=1, name='Chris Pine'),
          5: dict(id=5, character_id=2, name='Zachary Quinto'),
          6: dict(id=6, character_id=3, name='Karl Urban'),
      },
  }

And actor will have a reference to the played character - ``character_id``.

.. code-block:: python

  def get_character_data(fields: List[hiku.query.Field], ids: List[int]) \
          -> List[List[Any]]:
      result = []
      for id_ in ids:
          character = data['character'][id_]
          result.append([character[field.name] for field in fields])
      return result

  def get_actor_data(fields: List[hiku.query.Field], ids: List[int]) \
          -> List[List[Any]]:
      result = []
      for id_ in ids:
          actor = data['actor'][id_]
          result.append([actor[field.name] for field in fields])
      return result

  def actors_link(ids: List[int]) -> List[List[int]]:
      """Function to map character id to the list of actor ids"""
      mapping = defaultdict(list)
      for row in data['actor'].values():
          mapping[row['character_id']].append(row['id'])
      return [mapping[id_] for id_ in ids]

  def character_link(ids: List[int]) -> List[int]:
      """Function to map actor id to the character id"""
      mapping = {}
      for row in data['actor'].values():
          mapping[row['id']] = row['character_id']
      return [mapping[id_] for id_ in ids]

  graph = Graph([
      Edge('character', [  # 1
          Field('id', get_character_data),  # 2
          Field('name', get_character_data),
          Field('species', get_character_data),
          Link('actors', Many, actors_link,  # 3
               edge='actor', requires='id'),
      ]),
      Edge('actor', [  # 4
          Field('id', get_actor_data),
          Field('name', get_actor_data),
          Link('character', One, character_link,  # 5
               edge='character', requires='id'),
      ]),
      Root([
          Field('datetime', lambda _: [datetime.now().isoformat()]),
          Link('characters', Many, lambda: [1, 2, 3],
               edge='character', requires=None),
      ]),
  ])

Here ``actors`` :py:class:`~hiku.graph.Link` :sup:`[3]`, defined in the
``character`` edge :sup:`[1]`, requires ``id`` field :sup:`[2]` to map characters
to actors. That's why ``id`` field :sup:`[2]` was added to the ``character`` edge
:sup:`[1]`. The same work should be done in the ``actor`` edge :sup:`[4]` to
implement backward ``character`` link :sup:`[5]`.

Now we can include linked edge fields in our query:

.. code-block:: clojure

  [{:characters [:name {:actors [:name]}]}]

Result would be:

.. code-block:: javascript

  {
    "characters": [
      {
        "name": "James T. Kirk",
        "actors": [
          {
            "name": "William Shatner"
          },
          {
            "name": "Chris Pine"
          }
        ]
      },
      { ... },
      { ... }
    ]
  }

We can go further and follow ``character`` link from the ``actor`` edge
and return fields from ``character`` edge. This is an example of the
cyclic links, which is normal when this feature is desired for us, as long
as query is a hierarchical finite structure and result follows
it's structure.

.. code-block:: clojure

  [{:characters [:name {:actors [:name {:character [:name]}]}]}]

Result with cycle:

.. code-block:: javascript

  {
    "characters": [
      {
        "name": "James T. Kirk",
        "actors": [
          {
            "name": "William Shatner",
            "character": {
              "name": "James T. Kirk"
            }
          },
          {
            "name": "Chris Pine",
            "character": {
              "name": "James T. Kirk"
            }
          }
        ]
      },
      { ... },
      { ... }
    ]
  }

Conclusions
~~~~~~~~~~~

1. Now you know how to describe data as graph;
2. You can present in graph any data from any source.
