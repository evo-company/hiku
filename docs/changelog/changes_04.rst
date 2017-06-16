Changes in 0.4
==============

0.4.0
~~~~~

  - Refactored data sources to be simpler to setup and more consistent
  - Graph validation now performed automatically
  - Added :py:func:`hiku.graph.apply` function to apply graph transformers
  - Added :py:func:`hiku.validate.query.validate` function to simplify query
    validation


Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - ``primary_key`` argument in :py:class:`hiku.sources.sqlalchemy.FieldsQuery`
    now is keyword-only

  - :py:class:`hiku.sources.sqlalchemy.Field` removed, use
    :py:class:`hiku.graph.Field` instead:

    .. code-block:: python

      hiku.sources.sqlalchemy.Field('foo', fields_query)

    Changed to:

    .. code-block:: python

      hiku.graph.Field('foo', None, fields_query)

  - :py:class:`hiku.sources.sqlalchemy.LinkQuery` now doesn't needs a first
    ``type`` argument:

    .. code-block:: python

      character_to_actors_query = LinkQuery(
          Sequence[TypeRef['actor'],
          SA_ENGINE_KEY,
          from_column=actor_table.c.character_id,
          to_column=actor_table.c.id,
      )

    Changed to:

    .. code-block:: python

      character_to_actors_query = LinkQuery(
          SA_ENGINE_KEY,
          from_column=actor_table.c.character_id,
          to_column=actor_table.c.id,
      )

  - :py:class:`hiku.sources.sqlalchemy.Link` removed, use
    :py:class:`hiku.graph.Link` instead:

    .. code-block:: python

      hiku.sources.sqlalchemy.Link('actors', character_to_actors_query,
                                   requires='id')

    Changed to:

    .. code-block:: python

      hiku.graph.Link('actors', Sequence[TypeRef['actor']],
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
