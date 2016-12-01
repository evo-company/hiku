**Hiku** is a library to design *Graph API*

`Documentation <http://hiku.readthedocs.io/en/latest/>`_ |
`Example <https://github.com/vmagamedov/sw.kinko>`_

.. __boundary__

Why graphs? – They are simple, predictable, flexible, easy to compose and
because of that, they are easy to reuse.

`Hiku` is intended to be an answer for the questions about how to efficiently
pull data from your services via Graph API and how to implement this API
in your services with performance and flexibility in mind.

Features
~~~~~~~~

★ Express all your data sources as graph of nodes with fields and links.
You are free to choose between sync **threads/greenlets** and async
**coroutines** styles for data loading in your application. In both cases
`Hiku` can load data **concurrently** to speed-up overall graph queries.
Of course this is optional feature, and you are not required to rewrite
your code in order to use this feature later, code is initially written
in a way to make possible to run it concurrently.

★ Query your graph using `simple` queries or using GraphQL_ (partially
supported). This is how client can express its needs and avoid data
under-fetching or data over-fetching. Client will load only what it currently
needs using one query, instead of multiple queries to different *resources* (as
in RESTful APIs, for example). `Simple` queries are basically a data structures
in edn_ format. For example:

.. code-block:: clojure

    [{:characters [:name :species]}]

Corresponding `GraphQL` query will look like this:

.. code-block:: javascript

    {
        characters {
            name
            species
        }
    }

And result of these queries will look like this:

.. code-block:: javascript

    {
        "characters": [
            {
                "name": "James T. Kirk",
                "species": "Human"
            },
            {
                "name": "Spock",
                "species": "Vulcan/Human"
            },
            {
                "name": "Leonard McCoy",
                "species": "Human"
            }
        ]
    }

★ Abstract implementation details of how and where data actually stored,
by using concept of `Two-level Graph` and `Hiku's` expressions language.
This lets you define **low-level** graph to express all your data
sources as is, and **high-level** graph to express your business-logic
above low-level graph. High-level graph will use expressions to collect
and transform data from low-level graph.

.. _GraphQL: http://facebook.github.io/graphql/
.. _edn: https://github.com/edn-format/edn
