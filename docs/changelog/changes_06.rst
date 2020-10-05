Changes in 0.6
==============

0.6.1rcX
~~~~~~~~

  - Dropped Python 3.5 support
  - Added SQLAlchemy's asyncio support
  - Enhanced error message in the expression type checker
  - Fixed ``LinkQuery.select_expr()`` method to filter only ``None`` values
  - Engine ``Context`` now fully supports ``Mapping`` interface

0.6.0
~~~~~

  - Fixed Python 3.8 support
  - Added GraphQL query exporter
  - Fixed options serialization in the "simple" query exporter
  - Added ability to specify ``TypeRef`` using strings
  - Added Prometheus metrics support
  - Representing data types as Object type in GraphQL introspection
  - Implemented @skip and @include directives
  - Added GraphQL endpoint classes to incorporate the whole workflow
    of executing GraphQL queries
  - Added ``graphql_flask.py`` example
  - Made ``loop`` argument optional in ``AsyncIOExecutor``
  - Reimplemented denormalization functionality, which also fixes GraphQL
    introspection
  - ``AsyncIOExecutor`` now supports cancellation of sub-tasks
  - Optimized ``aiopg`` data source to use ``ANY`` op instead of ``IN`` op and
    to perform several ``fetchmany`` calls instead of one ``fetchall`` call
    to reduce event loop blocking

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Removed ``hiku.writers`` functionality
  - Switched from ``graphql-core`` to the ``graphql-core-next`` library
    for parsing GraphQL queries
  - Dropped Python 2.7 support, minimum supported version now is Python 3.5
