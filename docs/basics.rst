Basics
======

Here we will try to describe our first graph. To begin with we will need to
setup an environment:

.. code-block:: shell

    $ pip install hiku

Simplest one-field graph
~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: Source code of this example can be found
    `on GitHub <https://github.com/evo-company/hiku/blob/master/docs/basics/test_stage1.py>`_.

Let's define graph with only one field, which is easy to compute, for example it
would be a current time:

.. literalinclude:: basics/test_stage1.py
    :lines: 3-11

This is the simplest :py:class:`~hiku.graph.Graph` with one
:py:class:`~hiku.graph.Field` in the :py:class:`~hiku.graph.Root` node.

.. note:: We are using lambda-function and ignoring it's first argument because
    this function is used to load only one field and this field in the
    :py:class:`~hiku.graph.Root` node. In other cases you will need to use this
    and possibly other required arguments.

Then this field could be queried using this query:

.. code-block:: graphql

    { now }

To perform this query let's define a helper function ``execute``:

.. literalinclude:: basics/test_stage1.py
    :lines: 15-26

Then we will be ready to execute our query:

.. literalinclude:: basics/test_stage1.py
    :lines: 38-39
    :dedent: 4

You can also test this graph using special web console application, this is how
to setup and run it:

.. literalinclude:: basics/test_stage1.py
    :lines: 43-50

Then just open http://localhost:5000/ url in your browser and perform query from
the console.

Introducing nodes and links
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: Source code of this example can be found
    `on GitHub <https://github.com/evo-company/hiku/blob/master/docs/basics/test_stage2.py>`_.

This is cool, but what if we want to return some application data? First of all
lets define our data:

.. literalinclude:: basics/test_stage2.py
    :lines: 3-9

.. note:: For simplicity we will use in-memory data structures to store our
    data. How to load data from more sophisticated sources like databases will
    be explained in the next chapters.

Then lets define our graph with one :py:class:`~hiku.graph.Node` and one
:py:class:`~hiku.graph.Link`:

.. literalinclude:: basics/test_stage2.py
    :lines: 13-39
    :linenos:
    :emphasize-lines: 8,15,20-21,24-25

``character_data`` function :sup:`[8]` is used to resolve values for two fields
in the ``Character`` node. As you can see, it returns basically a list of lists
with values in the same order as it was requested in arguments (**order of ids and
fields should be preserved**).

This function used twice in the graph :sup:`[20-21]` -- for two fields, this is
how `Hiku` understands that both these fields can be loaded using this one
function and one function call. `Hiku` **groups fields by function, to load them
together.**

This gives us ability to resolve many fields for many objects (ids) using just
one simple function (when possible) to efficiently load data without introducing
lots of queries (to eliminate ``N+1`` problem, for example).

``to_characters_link`` function :sup:`[15]` is used to make a link
:sup:`[24-25]` from the :py:class:`~hiku.graph.Root` node to the ``Character``
node. This function should return character ids.

So now you are able to try this query in the console:

.. code-block:: graphql

  { characters { name species } }

Or in the program:

.. literalinclude:: basics/test_stage2.py
    :lines: 53-69
    :dedent: 4

Linking node to node
~~~~~~~~~~~~~~~~~~~~

.. note:: Source code of this example can be found
    `on GitHub <https://github.com/evo-company/hiku/blob/master/docs/basics/test_stage3.py>`_.

Let's extend our data with one more entity - ``Actor``:

.. literalinclude:: basics/test_stage3.py
    :lines: 3-17

Where actor will have a reference to the played character -- ``character_id``.
We will also need ``id`` fields in both nodes in order to link them with each
other.

Here is our extended graph definition:

.. literalinclude:: basics/test_stage3.py
    :lines: 21-73
    :linenos:
    :emphasize-lines: 20,26,36,37,40-41,43,46-47

Here ``actors`` :py:class:`~hiku.graph.Link` :sup:`[40-41]`, defined in the
``Character`` node :sup:`[36]`, ``requires='id'`` field :sup:`[37]` to map
characters to actors. That's why ``id`` field :sup:`[37]` was added to the
``Character`` node :sup:`[36]`. The same work should be done in the ``Actor``
node :sup:`[43]` to implement backward ``character`` link :sup:`[46-47]`.

``requires`` argument can be specified as a list of fields, in this case
``Hiku`` will resolve all of them and pass a ``list`` of ``dict`` to resolver.

``character_to_actors_link`` function :sup:`[20]` accepts ids of the characters
and should return list of lists -- ids of the actors, in the same order, so
every character id can be associated with a list of actor ids. This is how
**one to many** links works.

``actor_to_character_link`` function :sup:`[26]` requires/accepts ids of the
actors and returns ids of the characters in the same order. This is how
**many to one** links works.

So now we can include linked node fields in our query:

.. literalinclude:: basics/test_stage3.py
    :lines: 90-103
    :dedent: 4

We can go further and follow ``character`` link from the ``Actor`` node and
return fields from ``Character`` node. This is an example of the cyclic links,
which is normal when this feature is desired, as long as query is a hierarchical
finite structure and result follows it's structure.

.. literalinclude:: basics/test_stage3.py
    :lines: 106-127
    :dedent: 4
    :linenos:
    :emphasize-lines: 9,11,13

As you can see, there are duplicate entries in the result :sup:`[9,11,13]` --
this is how our cycle can be seen, the same character `Spock` seen multiple
times.
