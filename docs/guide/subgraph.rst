Two-level graph
===============

Two-level graph is a way to express business-logic once and provide it
on-demand.

Prerequisites
~~~~~~~~~~~~~

In order to show this feature we will try to adapt our
:doc:`previous example <database>`, ``actor`` table was removed and ``image``
table was added:

.. literalinclude:: subgraph.py
    :lines: 3-35

Low-level graph definition
~~~~~~~~~~~~~~~~~~~~~~~~~~

Low-level graph is a graph, which exposes all our data sources, database for example.
So this graph definition wouldn't be much different from our
:ref:`previous graph definition <guide-database-graph>`:

.. literalinclude:: subgraph.py
    :lines: 39-77
    :linenos:
    :emphasize-lines: 14,32-33

This example shows a :py:class:`~hiku.graph.Link` [32-33] with
:py:const:`~hiku.graph.Maybe` type. This is because column ``character.image_id``
can be equal to ``null``.

:py:const:`~hiku.graph.Maybe` type requires to use :py:const:`~hiku.graph.Nothing`
constant in the ``maybe_direct_link`` [14] function in order to indicate
that there is nothing to link to. This special constant is used instead of
``None``, because ``None`` can be a valid value.

For testing purposes let's define query helper function ``execute``:

.. literalinclude:: subgraph.py
    :lines: 81-92

So let's query some data, needed to show characters with their photos:

.. literalinclude:: subgraph.py
    :lines: 95-105
    :dedent: 4

What's wrong with this query?

.. code-block:: clojure

    [{:characters [:name {:image [:id :name]}]}]

Result of this query doesn't give us ready to use data representation - we
have to compute image url in order to show this information. Additionally, we have
to remember, that we should include query fragment ``{:image [:id :name]}`` in every
query, when we need to construct url for this image.

High-level graph definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

So our goal is to get rid of this implementation details and to be able to make
queries like this:

.. code-block:: clojure

    [{:characters [:name :image-url]}]

Instead of explicitly loading image data ``{:image [:id :name]}``, we want to
load ready-to-use image url. All we need is an ability to store information about
``image-url`` field computation and which data it needs for it's computation.

And here is when and why we need to implement two-level graph. Low-level graph
exposes all of our data sources. High-level graph is used to express our
business-logic based on low-level graph, and hide it's implementation details.

.. literalinclude:: subgraph.py
    :lines: 109-133
    :linenos:
    :emphasize-lines: 5-6,10,15,17-19

Hold on, as there are lots of new things in the high-level graph definition above.

:py:class:`~hiku.sources.graph.SubGraph` source [10] is used to refer to low-level
edge. Low-level edge and it's high-level counterpart are basically refer to the
same logical entity (`character`) and they share same unique identifiers
(``character.id``), used to identify every instance of the entity.

:py:class:`~hiku.sources.graph.SubGraph` is used along with
:py:class:`~hiku.sources.graph.Expr` fields to define expressions, which represent
how to compute high-level representation of data from low-level graph.

``S`` - is a special factory object, used to create symbols on the fly. ``S.foo``
means just ``foo``. It exists only because Python doesn't support custom symbols.

``S.this`` is a special case, it refers to the low-level counterpart of the current
edge. So ``S.this.name`` [15] is a ``name`` field of the ``character`` edge from the
low-level graph. As you can see, to expose low-level fields in the high-level edge
without modification, you just need to refer them using symbols with their names.

In order to make data modifications, we will need to use more complex expressions.
`Hiku` already has several built-in functions: :py:func:`~hiku.expr.each`,
:py:func:`~hiku.expr.if_` and :py:func:`~hiku.expr.if_some`. And you are able to use
your custom functions, :py:func:`~hiku.expr.define` decorator can be used to
define them.

As you can see, we defined ``image_url`` function [5-6] to compute image url, and
we declared types of arguments, which this function should accept. Here
``@define(Record[...])`` means that this function accepts one argument, which should
contain two fields - ``id`` and ``name``, and even that these fields should be with
specific types.

Type system and type checking plays a big role here. Expressions are declarative
and `Hiku` can analyze them in order to know which data from the low-level graph
should be loaded to compute high-level fields. When you request some fields in a
query to high-level graph, `Hiku` will automatically generate query for low-level
graph, this is how ``{:image [:id :name]}`` from ``:image-url`` magic happens.

And we also have to explain why we are using :py:func:`~hiku.expr.if_some`
function, before passing character's image into ``image_url`` function. It is used
because ``S.this.image`` is of type ``Optional[Record[...]]`` and it can't be passed
directly to the ``image_url`` function, which requires non-optional ``Record[...]``
type. :py:func:`~hiku.expr.if_some` function will unpack optional type into regular
type (as symbol ``S.img`` [18]) and then we can freely use it and be sure that
it's value wouldn't be ``None``.

Test:

.. literalinclude:: subgraph.py
    :lines: 138-148
    :dedent: 4
