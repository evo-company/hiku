Changes in 0.7
==============

0.7.0rcX
~~~~~~~~

  - Dropped support for Python 3.6, which ended support on 2021-12-23
  - Added support for Python 3.10
  - Added support for `Apollo Federation (v1) <https://www.apollographql.com/docs/federation/v1/>`_
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
  - Added mypy and typings to codebase
  - Added checks for unhashable link results and extend errors. This must improve developer experience.
  - Added caching for parsing graphql query. It is optional and can be enabled by calling :py:func:`hiku.readers.graphql.setup_query_cache`.
  - Added result cache - it is possible now to specify ``@cached`` directive to cache parts of the query. :ref:`Check cache documentation <caching-doc>`
  - ``Link(requires=['a', 'b'])`` can be specified as a list of strings. It is useful when you want to require multiple fields at once. It will pass a list of dicts to the resolver.
  - Added support for Python 3.11
  - Added hints when failing on unhashable return values
  - Migrated to ``pdm`` package manager
  - Reformat code with ``black``
  - Added support for Apollo Federation v2
  - Added support for custom schema directives :ref:`Check directives documentation <directives-doc>`
  - Added `ID` type.
  - Added support for unions :ref:`Check unions documentation <unions-doc>`
  - Added support for interfaces :ref:`Check interfaces documentation <interfaces-doc>`
  - Added support for enums :ref:`Check enums documentation <enums-doc>`
  - Added support for custom scalars :ref:`Check custom scalars documentation <scalars-doc>`

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Dropped Python 3.6 support, minimum supported version now is Python 3.7
  - Validate Option's default value. Now if `type` is not marked as `Optiona[...]` and `default=None`, validation will fail.
