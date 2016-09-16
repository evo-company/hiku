Basics
======

Here we will try to describe our first graph. To begin with we will need to
setup an environment:

.. code-block:: shell

    $ pip install hiku

Simplest one-field graph
~~~~~~~~~~~~~~~~~~~~~~~~

Let's define graph with only one field, which is easy to compute, for example it
would be a current time:

.. literalinclude:: basics/test_stage1.py
    :lines: 3-11

This is the simplest :py:class:`~hiku.graph.Graph` with one
:py:class:`~hiku.graph.Field` in the :py:class:`~hiku.graph.Root` edge.

.. note:: We are using lambda-function and ignoring it's first argument because
    this function is used to load only one field and this field in the
    :py:class:`~hiku.graph.Root` edge. In other cases you will need to use this
    and possibly other required arguments.

Then this field could be queried using this query:

.. code-block:: clojure

    [:now]

To perform this query let's define a helper function ``execute``:

.. literalinclude:: basics/test_stage1.py
    :lines: 15-25

Then we will be ready to execute our query:

.. literalinclude:: basics/test_stage1.py
    :lines: 34-35
    :dedent: 4

You can also test this graph using special web console application, this is how
to setup and run it:

.. literalinclude:: basics/test_stage1.py
    :lines: 39-46

Then just open http://localhost:5000/ url in your browser and perform query from
the console.

Introducing edges and links
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is cool, but what if we want to return some application data? First of all
lets define our data:

.. literalinclude:: basics/test_stage2.py
    :lines: 3-9

.. note:: For simplicity we will use in-memory data structures to store our
    data. How to load data from more sophisticated sources like databases will
    be explained in the next chapters.

Then lets define our graph with one :py:class:`~hiku.graph.Edge` and one
:py:class:`~hiku.graph.Link`:

.. literalinclude:: basics/test_stage2.py
    :lines: 13-38
    :linenos:
    :emphasize-lines: 7,14,19-20,23-24

``character_data`` function :sup:`[7]` is used to resolve values for two fields
in the ``character`` edge. As you can see, it returns basically a list of lists
with values in the same order as it was requested in arguments (order of ids and
fields should be preserved).

This function used twice in the graph :sup:`[19-20]` -- for two fields, this is
how `Hiku` understands that both these fields can be loaded using this one
function and one function call. `Hiku` groups fields by function, to load them
together.

This gives us ability to resolve many fields for many objects (ids) using just
one simple function (when possible) to efficiently load data without introducing
lots of queries (to eliminate ``N+1`` problem, for example).

``to_characters_link`` function :sup:`[14]` is used to make a link
:sup:`[23-24]` from the :py:class:`~hiku.graph.Root` edge to the ``character``
edge. This function should return character ids.

So now you are able to try this query in the console:

.. code-block:: clojure

  [{:characters [:name :species]}]

Or in the program:

.. literalinclude:: basics/test_stage2.py
    :lines: 50-66
    :dedent: 4

Linking edge to edge
~~~~~~~~~~~~~~~~~~~~

Let's extend our data with one more entity - ``actor``:

.. literalinclude:: basics/test_stage3.py
    :lines: 3-17

Where actor will have a reference to the played character -- ``character_id``.
We will also need ``id`` fields in both edges in order to link them with each
other.

Here is our extended graph definition:

.. literalinclude:: basics/test_stage3.py
    :lines: 21-72
    :linenos:
    :emphasize-lines: 19,25,35,36,39-40,42,45-46

Here ``actors`` :py:class:`~hiku.graph.Link` :sup:`[39-40]`, defined in the
``character`` edge :sup:`[35]`, requires ``id`` field :sup:`[36]` to map
characters to actors. That's why ``id`` field :sup:`[36]` was added to the
``character`` edge :sup:`[35]`. The same work should be done in the ``actor``
edge :sup:`[42]` to implement backward ``character`` link :sup:`[45-46]`.

``character_to_actors_link`` function :sup:`[19]` accepts ids of the characters
and should return list of lists -- ids of the actors, in the same order, so
every character id can be associated with a list of actor ids. This is how
**one to many** links works.

``actor_to_character_link`` function :sup:`[25]` requires/accepts ids of the
actors and returns ids of the characters in the same order. This is how
**many to one** links works.

So now we can include linked edge fields in our query:

.. literalinclude:: basics/test_stage3.py
    :lines: 89-102
    :dedent: 4

We can go further and follow ``character`` link from the ``actor`` edge and
return fields from ``character`` edge. This is an example of the cyclic links,
which is normal when this feature is desired, as long as query is a hierarchical
finite structure and result follows it's structure.

.. literalinclude:: basics/test_stage3.py
    :lines: 105-126
    :dedent: 4
    :linenos:
    :emphasize-lines: 11,13,15

As you can see, there are duplicate entries in the result :sup:`[11,13,15]` --
this is how our cycle can be seen, the same character `Spock` seen multiple
times.
