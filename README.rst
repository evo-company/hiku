Hiku
====

Hiku is a library to implement Graph APIs. Essential GraphQL support included.

Licensed under **BSD-3-Clause** license. See LICENSE.txt

Installation
~~~~~~~~~~~~

.. code-block:: shell

  $ pip3 install hiku

Bug fixes and new features are frequently published via release candidates:

.. code-block:: shell

  $ pip3 install --upgrade --pre hiku

Highlights
~~~~~~~~~~

* Not coupled to a single specific query language
* Flexibility in result serialization, including binary formats
* Natively uses normalized result representation, without data duplication
* All concurrency models supported: coroutines, threads
* Parallel query execution
* No data under-fetching or over-fetching between ``client<->server`` and
  between ``server<->database``
* No ``N+1`` problems by design
* Introduces a concept of `Two-Level Graph` in order to decouple data-sources
  and business-logic

Quick example
~~~~~~~~~~~~~

Graph definition:

.. code-block:: python

  from hiku.graph import Graph, Root, Node, Field, Link
  from hiku.types import String, Sequence, TypeRef

  def characters_data(fields, ids):
      data = {
          1: {'name': 'James T. Kirk', 'species': 'Human'},
          2: {'name': 'Spock', 'species': 'Vulcan/Human'},
          3: {'name': 'Leonard McCoy', 'species': 'Human'},
      }
      return [[data[i][f.name] for f in fields] for i in ids]

  def characters_link():
      return [1, 2, 3]

  GRAPH = Graph([
      Node('Character', [
          Field('name', String, characters_data),
          Field('species', String, characters_data),
      ]),
      Root([
          Link('characters', Sequence[TypeRef['Character']],
               characters_link, requires=None),
      ]),
  ])

Query:

.. code-block:: python

  from hiku.engine import Engine
  from hiku.builder import Q, build
  from hiku.executors.sync import SyncExecutor

  engine = Engine(SyncExecutor())

  result = engine.execute(GRAPH, build([
      Q.characters[
          Q.name,
          Q.species,
      ],
  ]))

  # use result in your code
  for character in result.characters:
      print(character.name, '-', character.species)

Output:

.. code-block:: text

  James T. Kirk - Human
  Spock - Vulcan/Human
  Leonard McCoy - Human

Contributing
~~~~~~~~~~~~

Use Tox_ in order to test and lint your changes.

.. _Tox: https://tox.readthedocs.io/
