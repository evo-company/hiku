Using AsyncIO :sup:`feat. aiopg`
================================

Hiku has several executors, previous examples were using
:py:class:`hiku.executors.sync.SyncExecutor` and they can also be used with
:py:class:`hiku.executors.threads.ThreadsExecutor` to execute query
concurrently using :py:class:`python:concurrent.futures.ThreadPoolExecutor`
without any change in the graph definition.

But, to be able to load data using :py:mod:`python:asyncio` library, all data
loading functions should be coroutines. We will translate one of the
:doc:`previous examples <database>` to show how to use :py:mod:`python:asyncio`
and aiopg_ libraries.

Prerequisites
~~~~~~~~~~~~~

.. note:: Source code of this example can be found
    `on GitHub <https://github.com/vmagamedov/hiku/blob/master/docs/test_asyncio.py>`_.

.. literalinclude:: test_asyncio.py
    :lines: 7-27

.. literalinclude:: test_asyncio.py
    :lines: 41-58
    :dedent: 4

Graph definition
~~~~~~~~~~~~~~~~

.. literalinclude:: test_asyncio.py
    :lines: 83-135
    :linenos:
    :emphasize-lines: 4,16,20,27

Note that we are using :py:mod:`hiku.sources.aiopg` source :sup:`[4]`
in our graph definition, instead of :py:mod:`hiku.sources.sqlalchemy`.

All our custom data loading functions :sup:`[16,20,27]` are coroutine
functions now and using :py:class:`aiopg:aiopg.sa.Engine` instead of
:py:class:`sqlalchemy:sqlalchemy.engine.Engine` to execute SQL queries.

Querying graph
~~~~~~~~~~~~~~

For testing purposes let's define helper coroutine function ``execute``:

.. literalinclude:: test_asyncio.py
    :lines: 139-149
    :linenos:
    :emphasize-lines: 10

Note that :py:meth:`hiku.engine.Engine.execute` method :sup:`[10]`
returns "awaitable" object, when it is using with
:py:class:`hiku.executors.asyncio.AsyncIOExecutor`. Here is how it
should be constructed:

.. literalinclude:: test_asyncio.py
    :lines: 153
    :dedent: 4

Testing one to many link:

.. literalinclude:: test_asyncio.py
    :lines: 154-181
    :dedent: 4

Testing many to one link:

.. literalinclude:: test_asyncio.py
    :lines: 186-216
    :dedent: 4

.. _aiopg: http://aiopg.readthedocs.io/en/stable/
