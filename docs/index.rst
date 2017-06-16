Hiku
====

Release v0.4 - :doc:`What's new <changelog/changes_04>`

Hiku is a library to design Graph APIs. Why graphs? – They are simple,
predictable, flexible, easy to compose and because of that, they are easy
to reuse.

Licensed under **BSD-3-Clause** license. See LICENSE.txt

Installation
~~~~~~~~~~~~

.. code-block:: shell

  $ pip install hiku

Highlights
~~~~~~~~~~

  * Not coupled to one specific query language
  * Flexibility in result serialization, including binary format
  * All concurrency models supported: async/await, threads, greenlets
  * Parallel execution of the query itself for free
  * No data under-fetching or over-fetching
  * No extra data loading from databases, only what was needed to fulfill
    the query
  * No ``N+1`` problems, they are eliminated by design
  * Even complex queries of any size are predictable in terms of
    performance impact
  * Implements a concept of the `Two-Level Graph` in order to put your
    business-logic in the right place

Quick example
~~~~~~~~~~~~~

.. container:: toggle

  .. container:: header

    Define your data (click to expand)

  .. literalinclude:: test_index.py
    :lines: 13-35

Define your graph:

.. literalinclude:: test_index.py
  :lines: 38-47

Express your needs using query:

.. tabs::

  .. group-tab:: GraphQL

    .. literalinclude:: test_index.py
      :language: javascript
      :lines: 52-57
      :dedent: 4

  .. group-tab:: Simple EDN

    .. literalinclude:: test_index.py
      :language: clojure
      :lines: 63
      :dedent: 4

  .. group-tab:: Python DSL

    .. literalinclude:: test_index.py
      :lines: 68-73
      :dedent: 4

Execute your query:

.. literalinclude:: test_index.py
  :lines: 79-80
  :dedent: 8

Denormalize result, so it will be possible to serialize into plain JSON
format:

.. literalinclude:: test_index.py
  :lines: 81
  :dedent: 8

And you will get ready for ``json.dumps`` result:

.. literalinclude:: test_index.py
  :language: javascript
  :lines: 83-98
  :dedent: 8

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
