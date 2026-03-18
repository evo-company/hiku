Schema
======

.. _schema-doc:

To create a schema you will need to define a graph and an choose an executor.

.. code-block:: python

    from hiku.graph import Graph, Root, Field
    from hiku.types import String
    from hiku.executors.sync import SyncExecutor

    def value_func(*_):
        return 'Hello, World!'

    graph = Graph([
        Root([
            Field('value', String, value_func),
        ]),
    ])

    schema = Schema(SyncExecutor(), graph)

Executing queries
-----------------

In order to execute query, run:

.. code-block:: python

    result = schema.execute_sync(query)


Or async execute:

.. code-block:: python

    result = await schema.execute(query)


To pass variables to the query:

.. code-block:: python

    result = await schema.execute(query, variables={'foo': 'bar'})

To run a query with a context:

.. code-block:: python

    result = await schema.execute(query, context={"db": db})

Executor
--------

Schema accepts :py:class:`hiku.executors.base.BaseExecutor` instance as a first argument. 

Schema will be able execute queries based on what executor you choose.

For example if you choose a :py:class:`hiku.executors.sync.SyncExecutor`, you will be able to execute queries synchronously:

.. code-block:: python

    result = schema.execute_sync({'value': None})
    print(result)

If you choose a :py:class:`hiku.executors.asyncio.AsyncIOExecutor`, you will be able to execute queries asynchronously:

.. code-block:: python

    result = await schema.execute({'value': None})
    print(result)

.. note::

   Its not recommended to use sync executors with async execute method and vise versa unless you are know what you are doing.

   In other words do not use ``SyncExecutor`` with :py:meth:`hiku.schema.Schema.execute`

   or ``AsyncExecutor`` with :py:meth:`hiku.schema.Schema.execute_sync`


Extensions
----------

Schema accepts a list of extensions passed to ``extensions`` argument:

.. code-block:: python

    schema = Schema(SyncExecutor(), graph, extensions=[CustomExtension()])
