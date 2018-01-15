Using GraphQL
=============

.. note:: Hiku is a general-purpose library to expose information as a graph. And
  initially, GraphQL support was not a primary concern. Hiku is an attempt to explore
  alternative ways without the need to conform to the GraphQL spec and implement all
  those features. So now, after several releases, it is possible to grow GraphQL
  support and keep it optional.

In order to parse GraphQL queries you will need to install ``graphql-core``
library:

.. code-block:: shell

  $ pip install graphql-core

**Currently not supported features**

- mutations and other non-query operations
- field aliases

Reading GraphQL queries
~~~~~~~~~~~~~~~~~~~~~~~

Minimal graph definition:

.. literalinclude:: test_graphql.py
  :lines: 11-25

GraphQL query execution:

.. literalinclude:: test_graphql.py
  :lines: 31-34
  :dedent: 4

Introspection
~~~~~~~~~~~~~

Hiku's graph by default doesn't contain a built-in introspection,
but it can be added.

.. note:: Hiku types are optional and are not fully compatible with GraphQL type
  system. For example, if the field contains :py:class:`~hiku.types.Any` or
  :py:class:`~hiku.types.Record` types, such fields will be ignored. You still
  will be able to query such fields, but they wouldn't be available for
  introspection.

For synchronous graphs:

.. literalinclude:: test_graphql.py
  :lines: 40-48
  :dedent: 4

For asynchronous graphs:

.. literalinclude:: test_graphql.py
  :lines: 59-67
  :dedent: 4
