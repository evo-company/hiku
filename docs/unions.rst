Unions
======

.. _unions-doc:

Union types are special types used to represent a value that could be one of types.

.. note:: Unlike interfaces, unions do not define any common fields between types.

In graphql you can use union types like this:

.. code-block:: graphql

    type Audio {
        id: ID!
        duration: Int!
    }

    type Video {
        id: ID!
        thumbnailUrl: String!
    }

    union Media = Audio | Video

    type Query {
        search(text: String!): [Media!]!
    }


In `hiku` you can use union types like this:

.. code-block:: python

    from hiku.graph import Union

    Union('Media', ['Audio', 'Video'])

Lets look at the full example on how to use unions in `hiku`:

.. code-block:: python

    from hiku.graph import Field, Graph, Link, Node, Root, Union
    from hiku.types import ID, Integer, String, TypeRef, Sequence, Optional, UnionRef

    def search_resolver():
        return [
            (1, TypeRef['Audio']),
            (2, TypeRef['Video']),
        ]

    unions = [
        Union('Media', ['Audio', 'Video']),
    ]

    GRAPH = Graph([
        Node('Audio', [
            Field('id', ID, audio_fields_resolver),
            Field('duration', Integer, audio_fields_resolver),
        ]),
        Node('Video', [
            Field('id', ID, video_fields_resolver),
            Field('thumbnailUrl', String, video_fields_resolver),
        ]),
        Root([
            Link('search', Sequence(UnionRef['Media']), search_resolver, requires=None),
        ]),
    ], unions=unions)

Lets look at the example above:

- ``Union`` type is defined with a list of types that are part of the union - ``Union('Media', ['Audio', 'Video'])``
- ``Link`` type is defined with a return type of ``Sequence[UnionRef['Media']]``
- ``search_resolver`` returns a list of tuples with an id as a first tuple element and type as a second tuple element

.. note::

    ``UnionRef`` is a special type that is used to reference union types. It is used in the example above to define
    the return type of the `search` link.

Now lets look at the query:

.. code-block:: graphql

    query {
        search(text: "test") {
            __typename
            ... on Audio {
                id
                duration
            }
            ... on Video {
                id
                thumbnailUrl
            }
        }
    }

As a result of the query above you will get a list of objects with `__typename` and `id` fields and fields that are specific
to the type of the object.

.. code-block:: json

    [
        {
            "__typename": "Audio",
            "id": 1,
            "duration": 100,
        },
        {
            "__typename": "Video",
            "id": 2,
            "thumbnailUrl": "http://example.com/thumbnail.jpg",
        },
    ]

Type narrowing
--------------

Unlike other graphql implementations `hiku` supports type narrowing without
``__resolveType`` function. It is possible because `hiku` knows all possible types
at the link resolution time.
