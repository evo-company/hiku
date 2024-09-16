Extensions
==========

.. _extensions-doc:

Extensions allow you to add custom functionality to your graph.

Extensions are classes that inherit from :class:`hiku.extensions.Extension`.

Each extension has a set of methods that are called at different stages of
graph processing.

Here are all the methods that can be implemented:

- :meth:`~hiku.extensions.Extension.on_init` - when schema is created
- :meth:`~hiku.extensions.Extension.on_operation` - when query is executed by the schema
- :meth:`~hiku.extensions.Extension.on_parse` - when query string is parsed into ast and the into query Node
- :meth:`~hiku.extensions.Extension.on_validate` - when query is validated
- :meth:`~hiku.extensions.Extension.on_execute` - when query is executed by engine

Custom extension
----------------

To write your own extension you need to inherit from :class:`hiku.extensions.Extension`
and implement methods that you need.

.. note::

    You can pass either instance or a class of the Extension to the schema's `extensions` argument.

    At runtime, if extension is a class, it will be instantiated by hiku.


Here is an example of custom extension that measures query execution time:

.. code-block:: python

    from typing import Iterator

    from hiku.extensions.base_extension import Extension
    from hiku.context import ExecutionContext

    class TimeItExtension(Extension):
        def on_execute(self, execution_context: ExecutionContext) -> Iterator[None]:
            start = time.perf_counter()
            yield
            print('Query execution took {:.3f} seconds'.format(time.perf_counter() - start))

    schema = Schema(graph, extensions=[TimeItExtension()])

In this example we use :class:`hiku.extensions.Extension` as a base class, and implement
:meth:`~hiku.extensions.Extension.on_execute` method.

This method is called when query is executed by the engine. So we measure the time
before and after the execution and print the result.

Built-in extensions
-------------------

QueryParseCache
~~~~~~~~~~~~~~~

Hiku uses ``graphql-core`` library to parse queries. But parsing same query again and again is a waste of resources and time.

Hiku provides a way to cache parsed queries. To enable it, you need to use ``QueryParseCache`` extensions.

.. code-block:: python

    schema = Schema(
        graph,
        extensions=[QueryParserCache(maxsize=50)],
    )

Note than for cache to be effective, you need to separate query and variables, otherwise
cache will be useless.

Query with inlined variables is bad for caching.

.. code-block:: graphql

    query User {
        user(id: 1) {
            name
            photo(size: 50)
        }
    }

Query with separated variables is good for caching.

.. code-block:: graphql

    query User($id: ID!, $photoSize: Int) {
        user(id: $id) {
            name
            photo(size: $photoSize)
        }
    }

**QueryParseCache** exposes metrics for query parsing time:

.. code-block:: python

    Gauge('hiku_query_cache_hits', 'Query cache hits')
    Gauge('hiku_query_cache_misses', 'Query cache misses')

QueryValidationCache
~~~~~~~~~~~~~~~~~~~~

``QueryValidationCache`` caches query validation result.

QueryDepthValidator
~~~~~~~~~~~~~~~~~~~

``QueryDepthValidator`` validates query depth. If query depth is greater than ``max_depth`` argument, it returns error
which says that query depth is too big.

.. code-block:: python

    schema = Schema(
        graph,
        extensions=[QueryDepthValidator(max_depth=10)],
    )

PrometheusMetrics
~~~~~~~~~~~~~~~~~

``PrometheusMetrics`` is a wrapper around ``GraphMetrics`` visitor. It exposes metrics for query execution time.

.. code-block:: python

    from hiku.extensions.prometheus import PrometheusMetrics
    schema = Schema(
        graph,
        extensions=[PrometheusMetrics('user_graph')],
    )

Custom metric
"""""""""""""

By default, ``PrometheusMetrics`` uses built-in metric ``graph_field_time``:

.. code-block:: python

    Summary("graph_field_time", "Graph field time (seconds)", ["graph", "node", "field"])

But you can pass your custom metric to ``PrometheusMetrics`` by using ``metric`` argument:

.. code-block:: python

    from prometheus_client import Gauge
    from hiku.extensions.prometheus import PrometheusMetrics

    metric = Histogram("my_custom_metric", "Graph field time (seconds)", ["graph", "node", "field"])

    schema = Schema(
        graph,
        extensions=[PrometheusMetrics('user_graph', metric=metric)],
    )

Custom labels
"""""""""""""

``PrometheusMetrics`` has ``ctx_var`` argument, which allows to pass custom ``ContextVar`` variable,
which will be set to **execution_context.context**. This can be used for example to use this context to expose different lables:

Here we adding new label ``os`` to the metric, and we want to use the ``os`` value from context:

.. code-block:: python

    from prometheus_client import Gauge
    from contextvars import ContextVar
    from hiku.extensions.prometheus import PrometheusMetrics

    metric = Histogram("my_custom_metric", "Graph field time (seconds)", ["graph", "node", "field", "os"])
    metrics_ctx = ContextVar('os')

    class CustomGraphqMetrics(GraphMetrics):
        def get_labels(
            self, graph_name: str, node_name: str, field_name: str, ctx: dict
        ) -> list:
            return [graph_name, node_name, field_name, ctx.get('os', 'unknown')]

    schema = Schema(
        graph,
        extensions=[
            PrometheusMetrics(
                'user_graph',
                metric=metric,
                ctx_var=metrics_ctx,
                transformer_cls=CustomGraphqMetrics
           )
        ],
    )

    endpoint = GraphQLEndpoint(schema)

    @app.post('/graphql')
    def graphql(request: Request):
        os = get_os(request)
        return endpoint.dispatch(request.body, context={'os': os})

PrometheusMetricsAsync
~~~~~~~~~~~~~~~~~~~~~~

``PrometheusMetricsAsync`` is a wrapper around ``AsyncGraphMetrics`` visitor. It exposes metrics for query execution time.

CustomContext
~~~~~~~~~~~~~

``CustomContext`` allows to define custom context for query execution.

If you do now want to pass context to `dispatch` method on every query, you can use :py:class:`hiku.extensions.context.CustomContext` extension,
which accepts a callback function, which will be called on every query execution and should return a context object:

.. code-block:: python

    db = Database()

    def get_context(execution_context: ExecutionContext) -> dict:
        return {'db': db}

    schema = Schema(
        graph,
        extensions=[CustomContext(get_context)]
    )

    result = schema.execute_sync(query)
