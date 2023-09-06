Using GraphQL
=============

.. note:: Hiku is a general-purpose library to expose data as a graph of linked
  nodes. And it is possible to implement GraphQL server using Hiku.

To implement GraphQL server we will have to add GraphQL introspection into our
graph and to add GraphQL query execution process:

  - read GraphQL query
  - validate query against graph definition
  - execute query using Engine
  - denormalize result into simple data structure
  - serialize result and send back to the client

Graph Definition
~~~~~~~~~~~~~~~~

GraphQL schema may have several root object types for each operation type:
query, mutation, subscription... Hiku has only one :py:class:`~hiku.graph.Root`
node to represent entry point into a graph. So, to implement mutations, we will
need a second :py:class:`~hiku.graph.Root` node, and second graph, which is
identical to the query graph, except :py:class:`~hiku.graph.Root` node:

.. code-block:: python

  query_graph = Graph([
      Root([
          Field('value', String, value_func),
      ]),
  ])

  mutation_graph = Graph(query_graph.nodes + [
      Root([
          Field('action', Boolean, action_func),
      ]),
  ])


Introspection
~~~~~~~~~~~~~

.. note:: Fields with underscore-prefixed names are hidden in GraphQL
  introspection.

.. automodule:: hiku.introspection.graphql
  :members: GraphQLIntrospection, AsyncGraphQLIntrospection

Incompatible with GraphQL types are represented as :py:class:`hiku.types.Any`
type.

``Record`` data types are represented as interfaces and input objects with
distinct prefixes. Given these data types:

.. code-block:: python

  graph = Graph([...], data_types={'Foo': Record[{'x': Integer}]})

You will see ``Foo`` data type via introspection as:

.. code-block:: javascript

  interface IFoo {
    x: Integer
  }

  input IOFoo {
    x: Integer
  }

This is because Hiku's data types universally can be used in field and
option definitions, as long as they don't have references to nodes.

Reading
~~~~~~~

In order to parse GraphQL queries you will need to install ``graphql-core``
library:

.. code-block:: shell

  $ pip install graphql-core

There are two options:

  - :py:func:`~hiku.readers.graphql.read` simple queries, when only query
    operations are expected
  - :py:func:`~hiku.readers.graphql.read_operation`, when different operations
    are expected: queries, mutations, etc.

.. automodule:: hiku.readers.graphql
    :members: read, read_operation, Operation, OperationType

Validation
~~~~~~~~~~

As every other query, GraphQL queries should be validated and errors can be
sent back to the client:

.. code-block:: python

  from hiku.validate.query import validate

  def handler(request):
      ... # read
      errors = validate(graph, query)
      if errors:
          return {'errors': [{'message': e} for e in errors]}
      ... # execute

Execution
~~~~~~~~~

Depending on operation type, you will execute query against one graph or
another:

.. code-block:: python

  if op.type is OperationType.QUERY:
      result = engine.execute_query(query_graph, op.query)
  elif op.type is OperationType.MUTATION:
      result = engine.execute_mutation(mutation_graph, op.query)
  else:
      return {'errors': [{'message': ('Unsupported operation type: {!r}'
                                      .format(op.type))}]}

Denormalization
~~~~~~~~~~~~~~~

Most common serialization format for GraphQL is JSON. But in order to serialize
execution result into JSON, it should be denormalized, to replace references
(possibly cyclic) with actual data:

.. code-block:: python

  from hiku.result import denormalize

  def handler(request):
      ... # execute
      result = {'data': denormalize(graph, result)}
      return jsonify(result)

.. _graphql-core: https://github.com/graphql-python/graphql-core


Query parsing cache
~~~~~~~~~~~~~~~~~~~

Hiku uses ``graphql-core`` library to parse queries. But parsing same query again and again is a waste of resources and time.

Hiku provides a way to cache parsed queries. To enable it, you need to use ``QueryParseCache`` extensions.

.. code-block:: python

    endpoint = GraphQLEndpoint(
        Engine(SyncExecutor()), sync_graph,
        extensions=[QueryParserCache(maxsize=50)],
    )

Note than for cache to be effective, you need to separate query and variables, otherwise
cache will be useless.

Query with inlined variables is bad for caching.

.. code-block:: python

    query User {
        user(id: 1) {
            name
            photo(size: 50)
        }
    }

Query with separated variables is good for caching.

.. code-block::

    query User($id: ID!, $photoSize: Int) {
        user(id: $id) {
            name
            photo(size: $photoSize)
        }
    }

    {
        "id": 1,
        "photoSize": 50
    }
