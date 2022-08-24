Telemetry
=========

Hiku exposes several prometheus metrics.

Graph execution time metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Shows the time spent in the graph execution for each Field or Link.

You can enable graph execution time metrics like this:

.. code-block:: python

  from hiku.telemetry import GraphMetrics
  from hiku.graph import Graph, Field, Root

  GRAPH = Graph([
      Root([
          Field('value', String, value_func),
      ]),
  ])

  metrics = GraphMetrics('mobile', metric=mobile_graph_metrics)
  GRAPH = metrics.visit(GRAPH)


Where:
 - *mobile* - is a graph label (in case you have multiple graphs in your app)
 - *metric* - is your custom Summary metric. If not provided, the default Summary('graph_field_time') is used

Default metric:

.. code-block:: python

    Summary(
        'graph_field_time',
        'Graph field time (seconds)',
        ['graph', 'node', 'field'],
    )


Query cache metrics
~~~~~~~~~~~~~~~~~~~

It is possible to enable query cache. That means that the same query will be parsed only once.

When query cache is enabled, the following metrics are exposed:

.. code-block:: python

    Gauge('hiku_query_cache_hits', 'Query cache hits')
    Gauge('hiku_query_cache_misses', 'Query cache misses')
