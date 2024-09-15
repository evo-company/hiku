Hiku
====

|project|_ |documentation|_ |version|_ |tag|_ |license|_

Hiku is a library to implement Graph APIs. Essential GraphQL support included.

Installation
~~~~~~~~~~~~

.. code-block:: shell

  $ pip3 install hiku

Bug fixes and new features are frequently published via release candidates:

.. code-block:: shell

  $ pip3 install --upgrade --pre hiku

Documentation
~~~~~~~~~~~~~

Read documentation_

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~

* `graphql-core` - for GraphQL support
* `sqlalchemy` - for SQLAlchemy support as a data-source
* `aiopg` - for async PostgreSQL support with `aiopg`
* `asyncpg` - for async PostgreSQL support with `asyncpg`
* `prometheus-client` - for Prometheus metrics support
* `sentry-sdk` - for Sentry tracing support


Highlights
~~~~~~~~~~

* Not coupled to a single specific query language
* Flexibility in result serialization
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

  from hiku.schema import Schema
  from hiku.builder import Q, build
  from hiku.executors.sync import SyncExecutor

  schema = Schema(SyncExecutor(), GRAPH)

  result = schema.execute_sync(build([
      Q.characters[
          Q.name,
          Q.species,
      ],
  ]))

  # use result in your code
  for character in result.data["characters"]:
      print(character["name"], '-', character["species"])

Output:

.. code-block:: text

  James T. Kirk - Human
  Spock - Vulcan/Human
  Leonard McCoy - Human

Contributing
~~~~~~~~~~~~

Use Tox_ in order to test and lint your changes.

.. _Tox: https://tox.readthedocs.io/
.. |project| image:: https://img.shields.io/badge/evo-company%2Fhiku-blueviolet.svg?logo=github
.. _project: https://github.com/evo-company/hiku
.. |documentation| image:: https://img.shields.io/badge/docs-hiku.rtfd.io-blue.svg
.. _documentation: https://hiku.readthedocs.io/en/latest/
.. |version| image:: https://img.shields.io/pypi/v/hiku.svg?label=stable&color=green
.. _version: https://pypi.org/project/hiku/
.. |tag| image:: https://img.shields.io/github/tag/evo-company/hiku.svg?label=latest
.. _tag: https://pypi.org/project/hiku/#history
.. |license| image:: https://img.shields.io/pypi/l/hiku.svg
.. _license: https://github.com/evo-company/hiku/blob/master/LICENSE.txt
