"""
hiku.query
==========

`Hiku` doesn't rely on any specific query language, internally it uses generic
data structures (query nodes) to describe result and they could be constructed
by parsing different suitable query languages.

However, `Hiku` provides one built-in way to describe result - `edn`_ data
structure (**HSQ** - Hiku Simple Query), similar to the `Datomic Pull API`_.

Why not to use `GraphQL`_ by default? `GraphQL` is complex due to the need to
write queries/fragments manually by hand. `HSQ` queries are not even queries,
they are just simple data structures - specifications of the result, they are
really easy to work with.

* ``[:foo]`` - edge fields definition (`edn` keywords in vector)
* ``{:bar [:baz]}`` - link definition (`edn` map with keyword and vector)
* ``(:foo {:key val})`` - field or link options definition (field name or
  link name, wrapped with `edn` list with map of options as a second value)

Example:

.. code-block:: clojure

  [:foo {:bar [:baz]}]

Here ``:foo`` and ``:baz`` are fields, ``:foo`` field is defined in the
``root`` edge, ``:baz`` field is defined in the edge, which is linked from
``root`` edge using ``:bar`` link.

More complex example:

.. code-block:: clojure

  [:a {:b [:c :d {:e [:f :g]}]} :h]

This query will return result like this:

.. code-block:: javascript

  {
    "a": ?,
    "b": [
      {
        "c": ?,
        "d": ?,
        "e": {
          "f": ?,
          "g": ?
        }
      },
      ...
    ],
    "h": ?
  }

By looking only at the query we can't predict types of the graph links,
in this example link ``:b`` is of type ``Many``, and link ``:e`` is
of type ``One`` or ``Maybe``.

.. _edn: https://github.com/edn-format/edn
.. _Datomic Pull API: http://docs.datomic.com/pull.html
.. _GraphQL: http://facebook.github.io/graphql/
"""
from itertools import chain
from collections import OrderedDict

from .utils import cached_property


def _name_repr(name, options):
    if options is None:
        return ':{}'.format(name)
    else:
        options_repr = ' '.join((':{} {!r}'.format(k, v)
                                 for k, v in options.items()))
        return '(:{} {{{}}})'.format(name, options_repr)


class Field(object):
    """
    *class* ``hiku.query.Field(name, options=None)``

    - ``name: str``
    - ``options: Optional[Mapping[str, Any]]``
    """
    def __init__(self, name, options=None):
        self.name = name
        self.options = options

    def __repr__(self):
        return _name_repr(self.name, self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class Link(object):
    """
    *class* ``hiku.query.Link(name, edge, options=None)``

    - ``name: str``
    - ``edge: hiku.query.Edge``
    - ``options: Optional[Mapping[str, Any]]``
    """
    def __init__(self, name, edge, options=None):
        self.name = name
        self.edge = edge
        self.options = options

    def __repr__(self):
        return '{{{} {!r}}}'.format(_name_repr(self.name, self.options),
                                    self.edge)

    def accept(self, visitor):
        return visitor.visit_link(self)


class Edge(object):
    """
    *class* ``hiku.query.Edge(fields)``

    - ``fields: Sequence[Union[hiku.query.Field, hiku.query.Link]]``
    """
    def __init__(self, fields):
        self.fields = fields

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self.fields)))

    def accept(self, visitor):
        return visitor.visit_edge(self)


def _merge(edges):
    seen = set()
    to_merge = OrderedDict()
    for field in chain.from_iterable(e.fields for e in edges):
        if field.__class__ is Link:
            to_merge.setdefault(field.name, []).append(field.edge)
        else:
            if field.name not in seen:
                seen.add(field.name)
                yield field
    for name, values in to_merge.items():
        yield Link(name, Edge(list(_merge(values))))


def merge(edges):
    return Edge(list(_merge(edges)))


class QueryVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        pass

    def visit_link(self, obj):
        self.visit(obj.edge)

    def visit_edge(self, obj):
        for item in obj.fields:
            self.visit(item)
