Changes in 0.5
==============

0.5.0
~~~~~

  - All query readers now return merged queries, so queries like this:

    .. code-block:: clojure

        [{:foo [:a :b]} {:foo [:b :c]}]

    will be transformed into this automatically:

    .. code-block:: clojure

        [{:foo [:a :b :c]}]

  - Added mutations support into GraphQL introspection
  - Added :py:func:`~hiku.readers.graphql.read_operation` function to support
    reading all GraphQL operations
  - Added ability to process nodes sequentially, as requested by a user
    in a query
  - Added aliases support into query builder
  - Heavily refactored result storage to eliminate cycling references
  - Result now also supports reading field values as attributes, in addition
    to the reading values by keys
  - Fixed query merge functionality to preserve options of the merged links
  - Fixed possible conflicts in the result's index
  - Implemented field alias support
  - Added Python 3.7 compatibility
  - Added ``Any`` type support for GraphQL introspection, this type also will
    be used for fields, which are incompatible with GraphQL's type system
  - Added ability to specify GraphQL operation name if client submits several
    operations in one document
  - Added ability to specify data types

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Removed ability to define Node in Root node in favor of complex types and
    data types
  - Added new positional argument to the
    :py:meth:`hiku.readers.graphql.GraphQLTransformer.transform` method
  - Renamed positional argument "pattern" in the
    :py:meth:`hiku.engine.Engine.execute` method
  - Removed third positional ``query`` argument in the
    :py:func:`hiku.result.denormalize` function
  - To add GraphQL introspection one should specify query graph and mutation
    graph during :py:class:`hiku.introspection.graphql.GraphQLIntrospection`
    or :py:class:`hiku.introspection.graphql.AsyncGraphQLIntrospection`
    initialization:

    .. code-block:: python

        graph = apply(graph, [GraphQLIntrospection(graph)])

Deprecated features
~~~~~~~~~~~~~~~~~~~

  - Data loading functions should return data as a ``list`` or as a similar
    type instead of returning generators. To use generators you can use a
    decorator link this:

    .. code-block:: python

        def listify(func):
            def wrapper(*args, **kwargs):
                return list(func(*args, **kwargs))
            return wrapper

        @listify
        def fields_func(fields, ids):
            for id in ids:
                ...
                yield row  # field values
