Changes in 0.7
==============

0.7.x
~~~~~

0.7.5
~~~~~

  - Add sqlalchemy 2 support in `PR-163 <https://github.com/evo-company/hiku/pull/163>` _

0.7.4
~~~~~

  - Fix `requires` as list if more that one Link with such `requires` is used in query
  - Migrate project to docker compose (v2)

0.7.3
~~~~~

  - Added support for Python 3.12
  - Fixed fragments merging. Previously we were merging fragments to aggresively, and it broke unions support in some cases. Fixed in `PR-151 <https://github.com/evo-company/hiku/pull/151>` _

0.7.2
~~~~~

  - Wrap functions in `hiku.telemetry.prometheus.py` to retain original function name in metrics
  - [fix] Add missing UnionRef to federation sdl generation

0.7.1
~~~~~

  - Fixed bug in graphql parser with undefined fragment used in query

0.7.0
~~~~~

  - Dropped support for Python 3.6, which ended support on 2021-12-23
  - Added support for Python 3.10
  - Added support for Python 3.11
  - Added support for `Apollo Federation (v1) <https://www.apollographql.com/docs/federation/v1/>`_
  - Added support for `Apollo Federation v2 (v2 is default now)`
  - [internal] Refactored introspection directives
  - Added graph schema directives support

    - Added ``directives`` argument to :py:class:`hiku.graph.Field`
    - Added ``directives`` argument to :py:class:`hiku.graph.Link`

  - Added ``Deprecated`` directive

    .. code-block:: python

          from hiku.directives import Deprecated

          graph = Graph([
              Root([
                  Field('lorem-ipsum', String, func,
                        options=[Option('words', Integer, default=50)],
                        directives=[Deprecated('use another field')]),
              ]),
          ])

    Or you can use ``deprecated`` argument to :py:class:`hiku.graph.Field`: or :py:class:`hiku.graph.Link`:

    .. code-block:: python

          from hiku.directives import Deprecated

          graph = Graph([
              Root([
                  Field('lorem-ipsum', String, func,
                        options=[Option('words', Integer, default=50)],
                        deprecated='use another field'),
              ]),
          ])

  - Added mypy and typings to codebase
  - Added checks for link results that can not be hashed and extend errors. This must improve developer experience.
  - Added result cache - it is possible now to specify ``@cached`` directive to cache parts of the query. :ref:`Check cache documentation <caching-doc>`
  - ``Link(requires=['a', 'b'])`` can be specified as a list of strings. It is useful when you want to require multiple fields at once. It will pass a list of dicts to the resolver.
  - Added hints when failing on return values that are not hashable
  - Migrated to ``pdm`` package manager
  - Reformat code with ``black``
  - Added support for custom schema directives :ref:`Check directives documentation <directives-doc>`
  - Added `ID` type.
  - Added support for unions :ref:`Check unions documentation <unions-doc>`
  - Added support for interfaces :ref:`Check interfaces documentation <interfaces-doc>`
  - Added support for enums :ref:`Check enums documentation <enums-doc>`
  - Added support for custom scalars :ref:`Check custom scalars documentation <scalars-doc>`
  - Added support for extensions :ref:`Check extensions documentation <extensions-doc>`

    - Added ``QueryParseCache`` extension - cache parsed graphql queries ast.
    - Added ``QueryTransformCache`` extension - cache transformed graphql ast into query Node.
    - Added ``QueryValidationCache`` extension - cache query validation.
    - Added ``QueryDepthValidator`` extension - validate query depth
    - Added ``PrometheusMetrics`` extension - wrapper around ``GraphMetrics`` visitor
    - Added ``PrometheusMetricsAsync`` extension - wrapper around ``AsyncGraphMetrics`` visitor

  - Add new method ``Engine.execute_context``, which accepts ``ExecutionContext``. ``Engine.execute`` now dispatches to ``Engine.execute_context``.
  - Add new method ``Engine.execute_mutation``, which allows to execute query against mutation graph
  - Add optional ``context`` argument to ``GraphqlEndpoint.dispatch`` method


Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Dropped Python 3.6 support, minimum supported version now is Python 3.7
  - Validate Option's default value. Now if `type` is not marked as `Optiona[...]` and `default=None`, validation will fail.
