Changes in 0.8
==============

0.8.0rc14
~~~~~~~~~

- Fix some broken type annotations


0.8.0rc13
~~~~~~~~~

- Fix using python ``Enum`` as ``Option.default`` value. SDL exporing was broken

0.8.0rc12
~~~~~~~~~

- Fix ``Optional[InputRef]`` value validation if None provided or argument not provided in query at all.


0.8.0rc11
~~~~~~~~~

- Fix Input Object default value serialization in introspection

0.8.0rc10
~~~~~~~~~

- Introduce ``InputObject`` types support (https://graphql.org/learn/schema/#input-object-types) via ``hiku.graph.Input`` and ``hiku.types.InputRef``

  ``Input`` is intended to supersed input objects generated from ``data_types`` Records (the one's with ``IO`` prefix).
  More on that in :ref:`Inputs docs <inputs-doc>`.

  .. code-block:: python

    from hiku.graph import Input
    from hiku.types import InputRef

    Graph([
      Node("User", [
        Field("id", Integer),
        Field("avatar", String, options=[
          Option("params", InputRef["ImageParams"])
        ])
      ]),
      Root([
        Field("user", TypeRef["User"]),
      ]),
    ], inputs=[
        Input("ImageParams", [
          Option("width", Integer),
          Option("height", Optional[Integer], default=None)
        ])
      ],
    )

0.8.0rc9
~~~~~~~~

- #181 Fix float input parsing when value is int

0.8.0rcX
~~~~~~~~

- Introduce ``Schema`` . This is a new high-level api with aim to provide single entrypoint for validation/execution
  and query/mutations. Previously we had to manage two serapate graphs - one for Query other for Mutation or use `endpoint`
  api but ``endpoint`` api is more like an integration-like api for http handlers. More on that in :ref:`Schema docs <schema-doc>`.
- ``Schema`` returns ``ExecutionResult`` dataclass with ``data``, ``errors`` and ``result`` fields. ``data`` already denormalized but access to `Proxy` object at ``result`` field is retained.
- ``Endpoint`` now is much simpler under the hood and it basically delegates execution to schema, only providing support for batching.
- Drop custom ``validate`` function for federation since we now have better support for ``_entities`` and ``_service`` fields and their corresponding types.
- Add new ``M`` query builder that indicates that this is a ``mutation``. It must be used to build a ``mutation`` query that will be passed to 
  ``Schema.execute`` method which will then infer that this is a mutation query Node.
- Drop ``hiku.federation.validate.validate``
- Drop ``hiku.federation.denormalize``
- Drop ``hiku.federation.engine``
- Drop ``hiku.federation.endpoint`` - use ``hiku.endpoint`` instead
- Change ``QueryDepthValidator`` hook to ``on_validate``
- Change ``GraphQLResponse`` type used by endpoint - it now has both ``data`` and ``errors`` fields
- Rename ``on_dispatch`` hook to ``on_operation``
- Remove ``execute`` method from ``BaseGraphQLEndpoint`` class
- Add ``process_result`` method to ``BaseGraphQLEndpoint`` class - it returns ``GraphQLResponse`` object with ``{"data": ...}`` or ``{"data": null, "errors": [...]`` is case ther are errors.
- Move ``GraphQLError`` to ``hiku.error`` module
- Drop ``GraphQLError.errors`` field. Earlier we used to store multiple errors in single ``GraphQLError`` but now its one message - one ``GraphQLError``.
- Add ``GraphQLError.message`` field
- Dropped support for ``Python 3.7``, which ended support on 2023-06-27
- Dropped support for ``Python 3.8``, which ended support on 2024-10-07
- Fix: now it is possible to alias record field
- Update pdm and migrate from pep528 to venv
- Use ``uv`` for faster package installation
- Add support for multiple types in ``representations`` in ``_entities`` federation field

  .. code-block:: python

    Graph([Root([Field("user", TypeRef["User"]))], data_types={"User": Record[{"id": Integer, "name": String}]})

  .. code-block:: graphql

    query {
      user {
        id
        my_name: name
      }
    }

- Drop ``loop`` parameter from ``hiku.executors.asyncio.AsyncIOExecutor`` constructor.


Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Drop `hiku.federation.endpoint.enormalize_entities`
- Drop `hiku.federation.validate.validate`
- Drop `hiku.federation.endpoint` - use `hiku.endpoint` instead
- Drop `hiku.federation.denormalize`
- Drop `hiku.federation.engine` - use `hiku.engine` instead
- Remove `execute` method from `BaseGraphQLEndpoint` class
- Move `GraphQLError` to `hiku.error` module
- Drop `GraphQLError.errors` field
- Add `GraphQLError.message` field
- Dropped support for Python 3.7, which ended support on 2023-06-27
- Dropped support for Python 3.8, which ended support on 2024-10-07
