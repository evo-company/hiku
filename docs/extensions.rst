Extensions
==========

.. _extensions-doc:

Extensions allow you to add custom functionality to your graph.

Extensions are classes that inherit from :class:`hiku.extensions.Extension`.

Each extension has a set of methods that are called at different stages of
graph processing.

Here are all the methods that can be implemented:

- :meth:`~hiku.extensions.Extension.on_graph` - when endpoint is created and transformations applied to graph
- :meth:`~hiku.extensions.Extension.on_operation` - when query is executed by the schema
- :meth:`~hiku.extensions.Extension.on_parse` - when query string is parsed into ast and the into query Node
- :meth:`~hiku.extensions.Extension.on_validate` - when query is validated
- :meth:`~hiku.extensions.Extension.on_execute` - when query is executed by engine

Built-in extensions
~~~~~~~~~~~~~~~~~~~

- ``QueryParseCache`` - cache parsed graphql queries ast.
- ``QueryValidationCache`` - cache query validation.
- ``QueryDepthValidator`` - validate query depth
- ``PrometheusMetrics`` - wrapper around ``GraphMetrics`` visitor
- ``PrometheusMetricsAsync`` - wrapper around ``AsyncGraphMetrics`` visitor
- ``CustomContext`` - allows to pass custom context to the query execution


Writing extension
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from typing import Iterator

    from hiku.extensions.base_extension import Extension
    from hiku.context import ExecutionContext

    class TimeItExtension(Extension):
        def on_execute(self, execution_context: ExecutionContext) -> Iterator[None]:
            start = time.perf_counter()
            yield
            print('Query execution took {:.3f} seconds'.format(time.perf_counter() - start))

    endpoint = GraphqlEndpoint(engine, graph, extensions=[TimeItExtension()])