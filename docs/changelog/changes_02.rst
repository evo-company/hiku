Changes in 0.2
==============

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Changed type of :py:attr:`hiku.graph.Field.options` from
  ``Mapping[str, Option]`` to ``Sequence[Option]``

- Changed type of :py:attr:`hiku.graph.Link.options` from
  ``Mapping[str, Option]`` to ``Sequence[Option]``

- Changed type of :py:attr:`hiku.graph.Edge.fields` from
  ``Mapping[str, Union[Field, Link]]`` to ``Sequence[Union[Field, Link]]``

- Changed type of :py:attr:`hiku.query.Edge.fields` from
  ``Mapping[str, Union[Field, Link]]`` to ``Sequence[Union[Field, Link]]``

- :py:class:`hiku.graph.Graph` is not a subclass of the
  :py:class:`hiku.graph.Edge` anymore, all the root edges,
  fields and links should be defined in the :py:class:`hiku.graph.Root`
  edge. Now :py:class:`hiku.graph.Graph` can contain only edges

- All :py:mod:`hiku.types` and :py:mod:`hiku.typedef.types` are now
  subclasses of ``type``, instead of being instances of ``type``

- Renamed :py:class:`hiku.types.Type` into :py:class:`hiku.types.GenericMeta`
- Renamed :py:class:`hiku.types.BooleanType` into :py:class:`hiku.types.Boolean`
- Renamed :py:class:`hiku.types.StringType` into :py:class:`hiku.types.String`
- Renamed :py:class:`hiku.types.IntegerType` into :py:class:`hiku.types.Integer`
- Renamed :py:class:`hiku.types.OptionType` into :py:class:`hiku.types.Optional`
- Renamed :py:class:`hiku.types.ListType` into :py:class:`hiku.types.Sequence`
- Renamed :py:class:`hiku.types.DictType` into :py:class:`hiku.types.Mapping`
- Renamed :py:class:`hiku.types.RecordType` into :py:class:`hiku.types.Record`
- Renamed :py:class:`hiku.types.FunctionType` into :py:class:`hiku.types.Callable`
- Removed :py:class:`hiku.types.ContainerType`
- Removed :py:func:`hiku.types.to_instance`

- Replaced required keyword argument ``to_list`` in the
  :py:class:`hiku.graph.Link` with second positional argument, which
  has a type of ``Union[Maybe, One, Many]``

- Replaced required keyword argument ``to_list`` in the
  :py:class:`hiku.sources.sqlalchemy.LinkQuery` with first positional
  argument, which has a type of ``Union[Maybe, One, Many]``

- Renamed required keyword argument and corresponding instance attribute
  from ``doc`` into ``description`` in the :py:class:`hiku.graph.Field`,
  :py:class:`hiku.graph.Link`, :py:class:`hiku.graph.Edge` and in the
  :py:class:`hiku.sources.sqlalchemy.Link` classes

- Renamed attribute of the :py:class:`hiku.typedef.kinko.TypeDoc`
  from ``__type_doc__`` into ``__type_description__``

- Moved constant :py:const:`hiku.engine.Nothing` to the
  :py:const:`hiku.graph.Nothing`

- Renamed attribute :py:attr:`hiku.result.Ref.storage` into
  :py:attr:`hiku.result.Ref.index`

- Renamed attribute :py:class:`hiku.result.State.idx` into
  :py:class:`hiku.result.State.index`

- :py:class:`hiku.sources.sqlalchemy.FieldsQuery` and
  :py:class:`hiku.sources.sqlalchemy.LinkQuery` now require context
  keys instead of "connectable" objects (SQLAlchemy's scoped session)

- Moved type :py:class:`hiku.typedef.types.Unknown` to the
  :py:class:`hiku.types.Unknown`

New features
~~~~~~~~~~~~

- Added ability to export :py:mod:`hiku.query` nodes. Added
  :py:mod:`hiku.export.simple` exporter, which will export query
  into EDN data structure

- Added debug mode for the :py:mod:`hiku.console` application,
  showing Python tracebacks if debug mode is turned on

- Implemented :py:class:`hiku.validate.query.QueryValidator`
  to validate query against graph definition before it's execution

- Implemented :py:class:`hiku.validate.graph.GraphValidator`
  to validate graph definition

- Added ability to define graph links with :py:const:`hiku.graph.Maybe`
  type, this link will conform to the :py:class:`hiku.types.Optional` type
  in the Hiku's type system:

  .. code-block:: python

    Link('link-to-foo', Maybe, func, edge='foo', requires=None)

- Added ability to query complex fields, which has a type of
  ``Optional[Record[...]]`` (Maybe), ``Record[...]`` (One) or
  ``Sequence[Record[...]]`` (Many) as if they were linked edges:

  .. code-block:: python

    Edge('foo', [
        Field('bar', Record[{'baz': Integer}], func),
    ])

  Here ``bar`` field should be queried as it was a link to the edge:

  .. code-block:: clojure

      [{:link-to-foo [{:bar [:baz]}]}]

- Added ability to use scalar values in the expressions. Currently
  only integer numbers and strings are supported:

  .. code-block:: python

    Expr('foo', foo_subgraph, func(S.this.foo, 'scalar'))

- Implemented :py:func:`hiku.expr.if_some` function in order to unpack
  :py:class:`hiku.types.Optional` type in expressions

- Added ability to pass objects, required to execute query, using bound
  to the query context:

  .. code-block:: python

    @pass_context
    def func(ctx, fields):
        return [ctx['storage'][f.name] for f in fields]

    Root([
        Field('foo', func),
    ])

    engine.execute(graph, read('[:foo]'),
                   ctx={'storage': {'foo': 1}})

- Implemented new :py:mod:`hiku.sources.aiopg` source for using aiopg_ and
  :py:class:`hiku.executors.asyncio.AsyncIOExecutor` to asynchronously
  load data from the `PostgreSQL` database

- Added ability to define function arguments using types instead of queries:

  .. code-block:: python

    @define(Record[{'foo': Integer}])  # instead of @define('[[:foo]]')
    def func(arg):
        return arg['foo'] + 1

.. _aiopg: http://aiopg.readthedocs.io/
