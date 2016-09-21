"""
    hiku.query
    ~~~~~~~~~~

    `Hiku` doesn't rely on any specific query language, internally it uses
    generic query representation to describe result and it could be constructed
    by parsing different suitable query languages.

    However, `Hiku` provides one built-in way to describe result -- `edn`_ data
    structure -- `simple` queries, which are very similar to the `om.next`_
    queries, which are inspired by `Datomic Pull API`_.

      - ``[:foo]`` - edge fields definition (`edn` keywords in vector)
      - ``{:bar [:baz]}`` - link definition (`edn` map with keyword and vector)
      - ``(:foo {:key val})`` - field or link options definition (field name or
        link name, wrapped with `edn` list with map of options as a second
        value)

    Example:

    .. code-block:: clojure

        [:foo {:bar [:baz]}]

    This query will be read internally as:

    .. code-block:: python

        Edge([Field('foo'),
              Link('bar', Edge([Field('baz')]))])

    And query result will look like this:

    .. code-block:: python

        {
            'foo': 1,
            'bar': {
                'baz': 2,
            },
        }

    .. _edn: https://github.com/edn-format/edn
    .. _Datomic Pull API: http://docs.datomic.com/pull.html
    .. _om.next: https://github.com/omcljs/om/wiki/Documentation-(om.next)
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
    """Represents a field of the edge

    :param name: name of the field
    :param optional options: field options -- mapping of names to values
    """
    def __init__(self, name, options=None):
        self.name = name
        self.options = options

    def __repr__(self):
        return _name_repr(self.name, self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class Link(object):
    """Represents a link to the edge

    :param name: name of the link
    :param edge: collection of fields and links --
                 :py:class:`~hiku.query.Edge`
    :param optional options: link options -- mapping of names to values
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
    """Represents collection of fields and links

    :param fields: list of :py:class:`~hiku.query.Field` and
                   :py:class:`~hiku.query.Link`
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
    """Merges multiple queries into one query

    :param edges: queries, represented as list of :py:class:`~hiku.query.Edge`
    :return: merged query as one :py:class:`~hiku.query.Edge`
    """
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
