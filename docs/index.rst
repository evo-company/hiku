**Hiku** is a library to design Graph APIs

.. toctree::
   :maxdepth: 2

   guide/index
   reference/index
   changelog/index

Why graphs? – They are simple, predictable, flexible, easy to compose and
because of that, they are easy to reuse.

Hiku is intended to be an answer for questions about how to speak to your
services, how to implement them and how to avoid ORMs usage.

Why not ORM? – Databases are too low level, they are implementation details of the
application/service. It is hard to abstract them properly, even with very smart and
sophisticated ORMs. Because again, databases are too low level and real-life
entities are not always possible or practical to map as 1:1 to the database schema.

::

    Every piece of knowledge must have a single, unambiguous, authoritative
    representation within a system.

– This is a quote from DRY principle, it says that
business logic (domain logic) should have only one single definition and
should be reused everywhere in the project. Here we are trying to make this possible
and practical to use.

Concepts
~~~~~~~~

Graphs are composed of edges, fields and links.

You can define fields, links and edges right in the implicit **root** of the
graph, which means that to access them, you do not need to know their
identity (ID), so they are singleton objects.

All other data (probably the largest) are represented in the form of a
network of edges, which should be referenced by identity and can only
be reached via a link.

There are two types of links: pointing to one object and pointing
to many objects.

Two-level Graph
~~~~~~~~~~~~~~~

This is how to properly abstract databases and other data sources into highly
reusable high-level entities.

You describe low-level graph to map your database as 1:1, every edge will be
a table, every field would be a column and every link will be a query,
to map one table to another.

High-level graph are edges with expressions instead of simple fields,
each expression describes how to compute high-level value using low-level graph. When you
are asking to retrieve some values from high-level graph, `hiku` generates a
query for the low-level graph, to retrieve minimal required data from database
to compute expressions in high-level graph.
