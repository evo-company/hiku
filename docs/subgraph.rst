Building Two-Level Graph
========================

Two-level graph is a way to express business-logic once and provide it
on-demand.

Prerequisites
~~~~~~~~~~~~~

.. note:: Source code of this example can be found
    `on GitHub <https://github.com/vmagamedov/hiku/blob/master/docs/test_subgraph.py>`_.

In order to show this feature we will try to adapt our
:doc:`previous example <database>`, ``actor`` table was removed and ``image``
table was added:

.. literalinclude:: test_subgraph.py
    :lines: 3-35

Low-level graph definition
~~~~~~~~~~~~~~~~~~~~~~~~~~

Low-level graph is a graph, which exposes all our data sources, database for
example. So this graph definition wouldn't be much different from our
:ref:`previous graph definition <guide-database-graph>`:

.. literalinclude:: test_subgraph.py
    :lines: 39-78
    :linenos:
    :emphasize-lines: 15,33-34

This example shows a :py:class:`~hiku.graph.Link` :sup:`[33-34]` with
:py:const:`~hiku.types.Optional` type. This is because column
``character.image_id`` can be equal to ``null``.

:py:const:`~hiku.types.Optional` type requires to use
:py:const:`~hiku.graph.Nothing` constant in the ``maybe_direct_link``
:sup:`[15]` function in order to indicate that there is nothing to link to. This
special constant is used instead of ``None``, because ``None`` can be a valid
value.

For testing purposes let's define helper function ``execute``:

.. literalinclude:: test_subgraph.py
    :lines: 82-93

So let's query some data, needed to show characters with their photos:

.. literalinclude:: test_subgraph.py
    :lines: 96-106
    :dedent: 4

What's wrong with this query?

.. code-block:: clojure

    [{:characters [:name {:image [:id :name]}]}]

Result of this query doesn't give us ready to use data representation - we have
to compute image url in order to show this information. Additionally, we have to
remember, that we should include query fragment ``{:image [:id :name]}`` in
every query, when we need to construct url for this image.

High-level graph definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

So our goal is to get rid of this implementation details and to be able to make
queries like this:

.. code-block:: clojure

    [{:characters [:name :image-url]}]

Instead of explicitly loading image data ``{:image [:id :name]}``, we want to
load ready-to-use image url. All we need is an ability to store information
about ``image-url`` field computation and which data it needs for it's
computation.

And here is when and why we need to implement two-level graph. Low-level graph
exposes all of our data sources. High-level graph is used to express our
business-logic based on low-level graph, and hides it's implementation details.

.. literalinclude:: test_subgraph.py
    :lines: 110-137
    :linenos:
    :emphasize-lines: 5-6,10,15,17-20

Hold on, as there are lots of new things in the high-level graph definition
above.

:py:class:`~hiku.sources.graph.SubGraph` source :sup:`[10]` is used to refer to
low-level node. Low-level node and it's high-level counterpart are basically
refer to the same logical entity (`character`) and they share same unique
identifiers (``character.id``), used to identify every instance of the entity.

:py:class:`~hiku.sources.graph.SubGraph` is used along with
:py:class:`~hiku.sources.graph.Expr` fields to define expressions, which
represent how to compute high-level representation of data from low-level graph.

``S`` - is a special factory object, used to create symbols on the fly.
``S.foo`` means just ``foo``. It exists only because Python doesn't support
unbound symbols.

``S.this`` is a special case, it refers to the low-level counterpart of the
current node. So ``S.this.name`` :sup:`[15]` is a ``name`` field of the
``character`` node from the low-level graph. As you can see, to expose low-level
fields in the high-level node without modification, you just need to refer them
using symbols with their names.

In order to make data modifications, we will need to use more complex
expressions. `Hiku` already has several built-in functions:
:py:func:`~hiku.expr.core.each`, :py:func:`~hiku.expr.core.if_` and
:py:func:`~hiku.expr.core.if_some`. And you are able to use your custom functions,
:py:func:`~hiku.expr.core.define` decorator should be used to make them suitable for
use in the `Hiku's` expressions.

As you can see, we defined ``image_url`` function :sup:`[6]` to compute image
url, and we declared argument types, which this function should accept, using
:py:func:`hiku.expr.core.define` decorator. Here ``@define(Record[...])`` :sup:`[7]`
means that decorated function accepts one argument (only positional arguments
are supported), which should be a record with at least two fields -- ``id`` and
``name``, and these fields should be with specified types:
:py:class:`~hiku.types.Integer` and :py:class:`~hiku.types.String`.

Type system and type checking plays a big role here. Expressions are declarative
and `Hiku` can analyze them in order to know which data from the low-level graph
should be loaded to compute high-level fields. When you request some fields in a
query to high-level graph (``:image-url``), `Hiku` will automatically generate
query for low-level graph (``{:image [:id :name]}``).

In our example above we can also see consequences of using type checking -- need
to use :py:func:`~hiku.expr.core.if_some` function :sup:`[17]` before passing
character's image into ``image_url`` function :sup:`[6]`. It is used because
``S.this.image`` is of type ``Optional[Record[...]]`` and it can't be passed
directly to the ``image_url`` function, which requires non-optional
``Record[...]`` type. :py:func:`~hiku.expr.core.if_some` function will unpack
optional type into regular type (bound to the symbol ``S.img`` :sup:`[17]`)
and then we can freely use it in the "then" clause of the
:py:func:`~hiku.expr.core.if_some` expression :sup:`[18]` and be sure that it's
value wouldn't be equal to ``None``. In the "else" clause we will return url
of the standard "no-photo" image :sup:`[19]`. Without using
:py:func:`~hiku.expr.core.if_some` function `Hiku` will raise type error.

Testing our high-level graph:

.. literalinclude:: test_subgraph.py
    :lines: 142-152
    :dedent: 4

As you can see, the goal is achieved.
