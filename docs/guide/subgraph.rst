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
    :lines: 3-36

Low-level graph definition
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: subgraph.py
    :lines: 40-79
    :linenos:
    :emphasize-lines: 33-34

Test helper:

.. literalinclude:: subgraph.py
    :lines: 83-94

Test:

.. literalinclude:: subgraph.py
    :lines: 97-104
    :dedent: 4

High-level graph definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: subgraph.py
    :lines: 108-134

Test:

.. literalinclude:: subgraph.py
    :lines: 139-149
    :dedent: 4
