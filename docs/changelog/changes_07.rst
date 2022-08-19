Changes in 0.7
==============

0.7.0rcX
~~~~~~~~

  - Dropped support for Python 3.6, which ended support on 2021-12-23
  - Added support for Python 3.10
  - Added support for `Apollo Federation (v1) <https://www.apollographql.com/docs/federation/v1/>`_
  - [internal] Refactored introspection directives
  - Added graph directives support

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

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Dropped Python 3.6 support, minimum supported version now is Python 3.7
