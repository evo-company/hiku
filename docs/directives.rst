Directives
==========

.. _directives-doc:

Graphql supports concept of directives. Directives are used to annotate various parts of schema.
For example in graphql schema you can use `@deprecated` directive to mark a field as deprecated.

There a two types of directions in graphql:

- Operation directives - used to annotate operations in query
- Schema directives - used to annotate schema types, fields, etc.

Operation directives
~~~~~~~~~~~~~~~~~~~~

Operation directives in GraphQL are utilized to alter the evaluation of schema elements or operations.
These operation directives can be incorporated into any GraphQL operation, including queries, subscriptions, or mutations.
They serve to modify either the operation's execution process or the values that the operation returns.

For example in graphql you can use
`@include` directive to include a field only if a given argument is true.

Built-in operation directives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hiku comes with a few built-in operation directives:

- `@include` - includes a field only if a given argument is true
- `@skip` - skips a field if a given argument is true
- `@cached` - caches a field for a given amount of time

Locations for Operation Directives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Operation directives must be used only in specific locations within the query.
These locations must be included in the directive's definition. In Strawberry, the location is defined in the directive function's parameter locations.

.. code-block:: python

   from hiku.directives import directive, Location
   @directive(locations=[Location.FIELD])

Operation Directives Locations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following list shows all allowed locations for operation directives:

- QUERY
- MUTATION
- SUBSCRIPTION
- FIELD
- FRAGMENT_DEFINITION
- FRAGMENT_SPREAD
- INLINE_FRAGMENT


Operation schema directives
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hiku does not allows create custom operation directives yet, but they are on our roadmap.

Schema directives
~~~~~~~~~~~~~~~~~

Hiku supports schema directives, which are directives that don't change the behavior of your GraphQL schema
but instead provide a way to add additional metadata to it.

.. note:: Apollo Federation integration is based on schema directives.

Built-in schema directives
~~~~~~~~~~~~~~~~~~~~~~~~~~

- `@deprecated` - marks a field as deprecated

Example of `@deprecated` directive in graphql

.. code-block:: graphql

    type Order {
        id: ID!
        state: String!
        status: Int! @deprecated(reason: "Use 'state' instead")
    }

In Hiku you can use `@deprecated` directive like this:

.. code-block:: python

    from hiku.graph import Graph, Field, Node
    from hiku.types import ID, Integer, String
    from hiku.directives import Deprecated

    GRAPH = Graph([
        Node('Order', [
            Field('id', ID, order_fields_resolver]),
            Field('state', String, order_fields_resolver]),
            Field('status', String, order_fields_resolver],
                  directives=[Deprecated("Use 'state' instead")]),
        ]),
    ])

Custom schema directives
~~~~~~~~~~~~~~~~~~~~~~~~

You can also define your own directives (reimplementation of `Deprecated` directive).

.. code-block:: python

    from hiku.graph import Graph, Field, Node
    from hiku.types import ID, Integer, String
    from hiku.directives import schema_directive, SchemaDirective, Location, schema_directive_field

    @schema_directive(
        name='deprecated',
        locations=[Location.FIELD_DEFINITION],
        description='Marks a field as deprecated',
    )
    class Deprecated(SchemaDirective):
        why: int = schema_directive_field(
            name='why',
            description='Why deprecated ?',
        )

    GRAPH = Graph([
        Node('Order', [
            Field('id', ID, order_fields_resolver]),
            Field('status', String, order_fields_resolver],
                  directives=[Deprecated("Old field")]),
        ]),
    ], directives=[Deprecated])

Note that type annotations for fields such as `why: int` are required, because `hiku`
will use them to generate types for schema introspection.

Also you can omit `name='why`, and `hiku` will then use the name of the field in the class automatically.