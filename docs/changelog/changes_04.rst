Changes in 0.4
==============

0.4.1
~~~~~

  - Fixed GraphQL introspection to describe also scalar types
  - Implemented expressions compilation for more scalar Python types, pull
    request courtesy Alex Koval
  - Fixed field options normalization, now with proper default values

0.4.0
~~~~~

  - Refactored data sources to be simpler to setup and more consistent
  - Graph validation now performed automatically
  - Added :py:func:`hiku.graph.apply` function to apply graph transformers
  - Added :py:func:`hiku.validate.query.validate` function to simplify query
    validation
  - Implemented complete options validation in the :py:mod:`hiku.validate.query`
  - Added :py:class:`hiku.types.Float` type
  - Fixed GraphQL introspection to properly encode default values
  - Fixed if_some expression compilation in Python 3.6
  - Fixed GraphQL query variables handling when they are optional
  - Fixed GraphQL introspection to properly encode null values
  - Added ability to specify option's description
  - Refactored type checking
  - Fixed linking from node to node without requirements
  - Changed options encoding format in ``hiku/protobuf/query.proto`` by using
    message types from ``google/protobuf/struct.proto`` instead of using custom
    types
  - Implemented result validation for the functions, used to load fields and
    links data

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - ``primary_key`` argument in :py:class:`hiku.sources.sqlalchemy.FieldsQuery`
    now is keyword-only

  - Renamed :py:class:`hiku.types.Unknown` into :py:class:`hiku.types.Any`

  - :py:class:`hiku.sources.sqlalchemy.Field` removed, use
    :py:class:`hiku.graph.Field` instead:

    .. code-block:: python

      hiku.sources.sqlalchemy.Field('foo', fields_query)

    Changed to:

    .. code-block:: python

      hiku.graph.Field('foo', None, fields_query)

  - :py:class:`hiku.sources.sqlalchemy.LinkQuery` now works with regular
    :py:class:`hiku.graph.Link` class, so :py:class:`hiku.sources.sqlalchemy.Link`
    was removed:

    .. code-block:: python

      character_to_actors_query = hiku.sources.sqlalchemy.LinkQuery(
          Sequence[TypeRef['Actor'],
          SA_ENGINE_KEY,
          from_column=actor_table.c.character_id,
          to_column=actor_table.c.id,
      )

      ... snip ...

      hiku.sources.sqlalchemy.Link('actors', character_to_actors_query,
                                   requires='id')

    Changed to:

    .. code-block:: python

      character_to_actors_query = hiku.sources.sqlalchemy.LinkQuery(
          SA_ENGINE_KEY,
          from_column=actor_table.c.character_id,
          to_column=actor_table.c.id,
      )

      ... snip ...

      hiku.graph.Link('actors', Sequence[TypeRef['Actor']],
                      character_to_actors_query, requires='id')

  - All the changes in :py:mod:`hiku.sources.sqlalchemy` are the same for
    :py:mod:`hiku.sources.aiopg` source

  - :py:class:`hiku.sources.graph.Expr` removed, use
    :py:class:`hiku.graph.Field` instead:

    .. code-block:: python

      Expr('foo', entity_sg, String, S.this.foo)

    Changed to:

    .. code-block:: python

      Field('foo', String, entity_sg.c(S.this.foo))

    Or even to:

    .. code-block:: python

      Field('foo', String, entity_sg)

  - Signature of the :py:meth:`hiku.validate.graph.GraphValidator.__init__`
    method changed. Graph validation now is not meant to be done manually and
    it was refactored to support validation of the graph before it would be
    actually created, by validating items, passed to the
    :py:class:`hiku.graph.Graph` constructor.

  - Replaced :py:func:`~hiku.introspection.graphql.add_introspection` and
    :py:func:`~hiku.introspection.graphql.add_introspection_async` functions with
    :py:class:`~hiku.introspection.graphql.GraphQLIntrospection` and
    :py:class:`~hiku.introspection.graphql.AsyncGraphQLIntrospection`
    respectively:

    .. code-block:: python

      graph = add_introspection_async(graph)

    Changed to:

    .. code-block:: python

      graph = hiku.graph.apply(graph, [AsyncGraphQLIntrospection()])

  - Due to changes in ``hiku/protobuf/query.proto``, field and link options,
    encoded using old format, will be ignored in the newer versions. Backward
    compatibility can be implemented on demand. Please create an Issue on
    GitHub, if you are using query encoding using Protocol Buffers and you will
    need a smooth upgrade path.
