Interfaces
==========

.. _interfaces-doc:

Interfaces are a special types that other types can implement.

Interfaces are useful when you want to define a common set of fields.

In graphql you can use interfaces types like this:

.. code-block::

    interface Media {
        id: ID!
        duration: String!
    }

    type Audio implements Media {
        id: ID!
        duration: String!
        album: String!
    }

    type Video implements Media {
        id: ID!
        duration: String!
        thumbnailUrl: String!
    }

    type Query {
        search(text: String!): [Media!]!
    }


In `hiku` you can define interface types like this:

.. code-block:: python

    from hiku.graph import Field, Interface
    from hiku.types import ID, String,
    from hiku.utils import empty_field

    Interface('Media', [
        Field('id', ID, empty_field),
        Field('duration', String, empty_field),
    ])

Lets look at full example on how to use interfaces in `hiku`:

.. code-block:: python

    from hiku.graph import Field, Graph, Link, Node, Root, Interface
    from hiku.types import ID, Integer, String, TypeRef, Sequence, Optional, InterfaceRef
    from hiku.utils import empty_field

    def search_resolver():
        return [
            (1, TypeRef['Audio']),
            (2, TypeRef['Video']),
        ]

    interfaces = [
        Interface('Media', [
            Field('id', ID, empty_field),
            Field('duration', String, empty_field),
        ]),
    ]

    GRAPH = Graph([
        Node('Audio', [
            Field('id', ID, audio_fields_resolver),
            Field('duration', String, audio_fields_resolver),
            Field('album', String, audio_fields_resolver),
        ], implements=['Media']),
        Node('Video', [
            Field('id', ID, video_fields_resolver),
            Field('duration', String, video_fields_resolver),
            Field('thumbnailUrl', String, video_fields_resolver),
        ], implements=['Media']),
        Root([
            Link('search', Sequence(UnionRef['Media']), search_resolver, requires=None),
        ]),
    ], interfaces=interfaces)

Lets decode the example above:

- ``Interface`` type is defined with a name and a list of fields that any implementation type must contain.
- ``Audio`` and ``Video`` types implement ``Media`` interface - they have ``id`` and ``duration`` field because ``Media`` interface declares them, and in addition to those shared fields each type has its own fields.
- ``Link`` type is defined with a return type of ``Sequence[InterfaceRef['Media']]``
- ``search_resolver`` returns a list of tuples with an id as a first tuple element and type as a second tuple element
- note that interface fields does need to have a resolver function, but currently this function is not used by hiku engine so you can pass ``empty_field`` as a resolver function (it may change in the future)

.. note::

    ``InterfaceRef`` is a special type that is used to reference interface types. It is used in the example above to define
    the return type of the `search` link. ``TypeRef`` will not work in this case.

If we run this query:

.. code-block:: python

    query {
        search(text: "test") {
            __typename
            id
            duration
            ... on Audio {
                album
            }
            ... on Video {
                thumbnailUrl
            }
        }
    }

As a result we will get a list of objects with ``__typename``, ``id`` and ``duration`` fields and fields that are specific
to the type of the object.

.. code-block::

    [
        {
            '__typename': 'Audio',
            'id': 1,
            'duration': '1:20',
            'album': 'Cool album',
        },
        {
            '__typename': 'Video',
            'id': 2,
            'duration': '1:40',
            'thumbnailUrl': 'http://example.com/thumbnail.jpg',
        },
    ]

Type narrowing
--------------

Unlike other graphql implementations `hiku` supports type narrowing without
``__resolveType`` function. It is possible because `hiku` knows all possible types
at the link resolution time.