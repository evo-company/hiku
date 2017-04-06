**Hiku** is a library to design Graph APIs. Why graphs? – They are simple,
predictable, flexible, easy to compose and because of that, they are easy
to reuse.

Documentation: https://hiku.readthedocs.io/

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

Contributing
~~~~~~~~~~~~

Please feel free to open an issue if you are getting mysterious error
messages. It will be much easier to track down bugs, if you will
provide short graph definition to reproduce it. Pull requests are highly
appreciated and awaited. Especially when it comes to a spelling errors
in documentation.

Use Tox_ in order to test and lint your changes.

.. _Tox: https://tox.readthedocs.io/
