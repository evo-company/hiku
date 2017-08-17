Using Protocol Buffers
======================

Query format
~~~~~~~~~~~~

It is possible to serialize queries using `Protocol Buffers`_ in binary form,
instead of sending it as a text in edn_ or GraphQL_ format.

Hiku has a :doc:`hiku/protobuf/query.proto <reference/protobuf/query>` file,
which describes message types for query serialization.

Here is how they can be used to build query:

.. literalinclude:: test_protobuf.py
    :lines: 20-28
    :dedent: 4

This query is equivalent to this query in edn_ format:

.. code-block:: clojure

    [{:characters [:name]}]

And is equivalent to this query in GraphQL_ format:

.. code-block:: javascript

    {
      characters {
        name
      }
    }

.. note:: Protocol Buffers has it's own ability to specify requirements for
    `get` operations -- ``google.protobuf.FieldMask``, but this approach has
    limitations for our use. For example, field options can't be expressed with
    field masks. So it would be hard to utilize field masks for our use case
    and that's why Hiku provides it's own message types for queries.

Query export
~~~~~~~~~~~~

In Python it is not required to use example above in order to build query using
Protocol Buffers message classes. Hiku provides handy
:py:func:`~hiku.export.protobuf.export` function to transform query into
Protocol Buffers message:

.. literalinclude:: test_protobuf.py
    :lines: 30-42
    :dedent: 4

Query reading
~~~~~~~~~~~~~

In order to execute query, Hiku provides :py:func:`~hiku.readers.protobuf.read`
function, which can be used to deserialize query from Protocol Buffers message:

.. literalinclude:: test_protobuf.py
    :lines: 52-56
    :dedent: 4

Result serialization
~~~~~~~~~~~~~~~~~~~~

The main advantage of using Hiku with Protocol Buffers is to give efficient
binary format for result serialization, which can be safely read in any other
language with Protocol Buffers support.

.. note:: Hiku is only suitable with latest 3rd version of Protocol Buffers
    format. This is because only in 3rd version of Protocol Buffers all message
    fields are *strictly optional*, and this opens possibility for clients to
    express their requirements and server will return only what client cares
    about.

Here is our example of a graph, similar to the one from :doc:`basics`:

.. literalinclude:: test_protobuf.py
    :lines: 7-16

This graph can be expressed like this in ``example.proto`` file:

.. literalinclude:: example.proto
    :language: proto

Now we can generate ``example_pb2.py`` file from ``example.proto`` by using
``protoc`` compiler. And this is how it can be used to serialize result:

.. literalinclude:: test_protobuf.py
    :lines: 62-75
    :dedent: 4

In this example server will compute only ``name`` field of the ``Character``
type, because this is the only field, which was specified in the query.

.. note:: Using Protocol Buffers "as is" still not the most efficient way to
    send result back to the client. Result is sent in denormalized form, so it
    contains duplicates of the same data. More efficient way would be more
    complicated and probably will be implemented in the future. See
    `Netflix/Falcor`_ and `Om Next`_ as examples of using normalized results.
    See also how Hiku stores result internally: :py:mod:`hiku.result`

.. _Protocol Buffers: https://github.com/google/protobuf
.. _GraphQL: http://facebook.github.io/graphql/
.. _edn: https://github.com/edn-format/edn
.. _Netflix/Falcor: http://netflix.github.io/falcor/
.. _Om Next: https://github.com/omcljs/om
