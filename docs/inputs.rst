Input Object types
==================

.. _inputs-doc:

Input object types are named types used to specify input arguments types.

Graphql specification https://graphql.org/learn/schema/#input-object-types

In graphql schema definition it is specified like this:

.. code-block:: graphql

    input CreateUser {
        name: String!
    }

Old-style input types
---------------------

Before Hiku ``0.0.8`` the only way to represent complex input types was by using ``data_types``.

When data type was created by hiku using ``Record[...]`` syntax like this:

.. code-block:: python

    Graph(..., data_types={"User": Record[{"id": Integer, "name": String}]})

it actually created two types:

#. One named ``User`` which is ``OBJECT`` type
#. Another named ``IOUser`` which is ``INPUT_OBJECT`` type

While it is quite easy to setup, this approach has some limitations:

1. It is implicit. There is no place in the code which says that ``User`` record data type will create two types, one of each will be input type with ``IO`` prefix
2. It does not allow to specify default values for individual ``Record`` fields


New-style input types
---------------------

Starting from ``0.0.8``, Hiku introduces new input object support via ``hiku.graph.Input`` and ``hiku.types.InputRef``

``Input`` is intended to supersed input objects generated from ``data_types`` records.

To create an input type, you need to pass a list of ``Input`` instances to Graph constructor like this ``Graph(..., inputs=inputs]``

To reference an input type, you need to use ``InputRef['NameOfInputType']`` as a type argument for ``Option``

Full example is provided below:

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

In the provided example we can see that new ``Input("ImageParams")`` is created and passed to ``inputs`` argument of ``Graph`` constructor.
Then ``ImageParams`` used as an input type in ``User.avatar`` option ``params`` via ``InputRef["ImageParams"]``


Input coercion
--------------

Hiku applies input coercion following the specification https://spec.graphql.org/draft/#sec-Input-Objects.Input-Coercion

Rules:


Required argument
~~~~~~~~~~~~~~~~~

.. code-block:: python

      Option("param", String)

* If value not provided, an error is raised


Optional argument
~~~~~~~~~~~~~~~~~

.. code-block:: python

      Option("param", Optional[String])

According to specification, there is a semantic difference between not providing value and providing value with ``null``:

* If value not provided, there will be no such key in options dict.

  This is done by specifying ``Option.default`` argument as ``hiku.types.Nothing`` which denotes value absense.

  ``Option.default`` keyword argument declared as ``Nothing`` by default.

* If value is provided as ``null``, resulting options dict will contain key with value ``None``

* If value is provided, resulting options dict will contain key with provided value


Optional argument with default
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

      Option("param", Optional[String], default="foo")


* If value not provided, resulting options dict will contain key with value specified in ``default``.

* If value is provided, resulting options dict will contain key with provided value
