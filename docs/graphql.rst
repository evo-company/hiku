Using GraphQL
=============

`Hiku` is trying to be simple so it doesn't support all the `GraphQL`
features.

In order to parse `GraphQL` queries you will need to install ``graphql-core``
library:

.. code-block:: shell

    $ pip install graphql-core

**Supported features**

- query documents with single query operation
- selection sets
- fields with arguments
- fragments
- variables

**Probably will be supported in the future**

- mutations and other non-query operations
- field aliases


Reading GraphQL queries
~~~~~~~~~~~~~~~~~~~~~~~

Minimal graph definition:

.. literalinclude:: test_graphql.py
    :lines: 11-25

`GraphQL` query execution:

.. literalinclude:: test_graphql.py
    :lines: 31-34
    :dedent: 4


Introspection
~~~~~~~~~~~~~

Hiku's graph by default doesn't contain a built-in introspection,
but it can be added.

For synchronous graphs:

.. literalinclude:: test_graphql.py
    :lines: 40-48
    :dedent: 4

For asynchronous graphs:

.. literalinclude:: test_graphql.py
    :lines: 59-67
    :dedent: 4
