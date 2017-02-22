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

**Probably will be supported in the future**

- mutations and other non-query operations
- field aliases
- variables

Reading GraphQL queries
~~~~~~~~~~~~~~~~~~~~~~~

Minimal graph definition:

.. literalinclude:: test_graphql.py
    :lines: 9-23

`GraphQL` query execution:

.. literalinclude:: test_graphql.py
    :lines: 29-32
    :dedent: 4
