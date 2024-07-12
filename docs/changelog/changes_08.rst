Changes in 0.8
==============

0.8.0rcX
~~~~~~~~

  - Introduce `Schema`. This is a new high-level api with aim to provide single entrypoint for validation/execution
    and query/mutations. Previously we had to manage two serapate graphs - one for Query other for Mutation or use `endpoint`
    api but `endpoint` api is more like an integration-like api for http handlers.
  - `Endpoint` now is much simpler under the hood and it basically delegates execution to schema, only providing support for batching.
  - Drop custom `validate` function for federation since we now have better support for `_entities` and `_service` fields and their corresponding types.
  - Add new `M` query builder that indicates that this is a `mutation`. It must be used to build a `mutation` query that will be passed to 
    `Schema.execute` method which will then infer that this is a mutation query Node.
  - Drop `hiku.federation.validate.validate`
  - Drop `hiku.federation.denormalize`
  - Drop `hiku.federation.engine`
  - Drop `hiku.federation.endpoint` - use `hiku.endpoint` instead
  - Merge `tests.test_federation.test_endpoint` and `tests.test_federation.test_engine` into `tests.test_federation.test_schema`
  - Change `QueryDepthValidator` hook to `on_validate`
  - Change `GraphQLResponse` type - it now has both `data` and `errors` fields
  - Rename `on_dispatch` hook to `on_operation`
  - Remove old `on_operation` hook

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  - Drop `hiku.federation.endpoint.enormalize_entities`
  - Drop `hiku.federation.validate.validate`
  - Drop `hiku.federation.endpoint` - use `hiku.endpoint` instead
  - Drop `hiku.federation.denormalize`
  - Drop `hiku.federation.engine` - use `hiku.engine` instead
