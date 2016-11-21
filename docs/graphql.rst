GraphQL support
===============

`Hiku` is trying to be simple so it doesn't support all the `GraphQL`
features.

In order to parse `GraphQL` queries you will need to install `graphql-core`
library:

.. code-block:: shell

    pip install graphql-core

or install `Hiku` library with extras:

.. code-block:: shell

    pip install hiku[graphql]

**Supported features**

- documents with single query operation
- selection sets
- fields with arguments

**Probably will be supported**

- field aliases

**Unsupported (intentionally)**

- mutations and other possible non-query operations
- multiple operations per document
- all the fragments-related features
- introspection
- directives
- interfaces
- variables
- unions
- enums

Reading GraphQL queries
~~~~~~~~~~~~~~~~~~~~~~~

Minimal graph definition:

.. literalinclude:: test_graphql.py
    :lines: 9-23

`GraphQL` query execution:

.. literalinclude:: test_graphql.py
    :lines: 29-32
    :dedent: 4
