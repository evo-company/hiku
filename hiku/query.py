"""
    hiku.query
    ~~~~~~~~~~

    `Hiku` doesn't rely on any specific query language, internally it uses
    generic query representation to describe result and it could be constructed
    by parsing different suitable query languages.

    However, `Hiku` provides one built-in way to describe result -- `edn`_ data
    structure -- `simple` queries, which are very similar to the `om.next`_
    queries, which are inspired by `Datomic Pull API`_.

      - ``[:foo]`` - node fields definition (`edn` keywords in vector)
      - ``{:bar [:baz]}`` - link definition (`edn` map with keyword and vector)
      - ``(:foo {:key val})`` - field or link options definition (field name or
        link name, wrapped with `edn` list with map of options as a second
        value)

    Example:

    .. code-block:: clojure

        [:foo {:bar [:baz]}]

    This query will be read internally as:

    .. code-block:: python

        Node([Field('foo'),
              Link('bar', Node([Field('baz')]))])

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
    """Represents a field of the node

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
    """Represents a link to the node

    :param name: name of the link
    :param node: collection of fields and links --
                 :py:class:`~hiku.query.Node`
    :param optional options: link options -- mapping of names to values
    """
    def __init__(self, name, node, options=None):
        self.name = name
        self.node = node
        self.options = options

    def __repr__(self):
        return '{{{} {!r}}}'.format(_name_repr(self.name, self.options),
                                    self.node)

    def accept(self, visitor):
        return visitor.visit_link(self)


class Node(object):
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
        return visitor.visit_node(self)


def _merge(nodes):
    seen = set()
    to_merge = OrderedDict()
    for field in chain.from_iterable(e.fields for e in nodes):
        if field.__class__ is Link:
            to_merge.setdefault(field.name, []).append(field.node)
        else:
            if field.name not in seen:
                seen.add(field.name)
                yield field
    for name, values in to_merge.items():
        yield Link(name, Node(list(_merge(values))))


def merge(nodes):
    """Merges multiple queries into one query

    :param nodes: queries, represented as list of :py:class:`~hiku.query.Node`
    :return: merged query as one :py:class:`~hiku.query.Node`
    """
    return Node(list(_merge(nodes)))


class QueryVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        pass

    def visit_link(self, obj):
        self.visit(obj.node)

    def visit_node(self, obj):
        for item in obj.fields:
            self.visit(item)
