Hiku
====

Hiku is a library to implement Graph APIs. GraphQL support included.

Licensed under **BSD-3-Clause** license. See LICENSE.txt

Installation
~~~~~~~~~~~~

.. code-block:: shell

  $ pip install hiku

Highlights
~~~~~~~~~~

  * Not coupled to a single specific query language
  * Flexibility in result serialization, including binary formats
  * Natively uses normalized result representation, without data duplication
  * All concurrency models supported: coroutines, threads
  * Parallelized query execution
  * No data under-fetching or over-fetching between ``client<->server`` and
    between ``server<->database``
  * No ``N+1`` problems by design
  * Introduces a concept of `Two-Level Graph` in order to decouple data-sources
    and business-logic

Quick example
~~~~~~~~~~~~~

Graph definition:

.. code-block:: python

  CHARACTER_DATA = {
      '819e79e09f40': {'name': 'James T. Kirk', 'species': 'Human'},
      '4266ffb4fbc3': {'name': 'Spock', 'species': 'Vulcan/Human'},
      'a562fedf8804': {'name': 'Leonard McCoy', 'species': 'Human'},
  }

  def characters_data(fields, ids):
      for ident in ids:
          yield [CHARACTER_DATA[ident][f.name] for f in fields]

  def characters_link():
      return ['819e79e09f40', '4266ffb4fbc3', 'a562fedf8804']

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

  engine = Engine(SyncExecutor())
  query = build([
      Q.characters[
          Q.name,
          Q.species,
      ],
  ])
  result = engine.execute(GRAPH, query)

  # use result in your code
  for character in result.characters:
      print(character.name)
      print(character.species)

  # get `json.dumps()`-ready result representation
  data = denormalize(GRAPH, result)
  assert data == {
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
          },
      ]
  }

User's Guide
~~~~~~~~~~~~

.. toctree::
  :maxdepth: 2

  basics
  database
  subgraph
  asyncio
  graphql
  protobuf
  reference/index
  changelog/index
