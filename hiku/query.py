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
from collections.abc import Sequence

from .utils import cached_property


def _compute_hash(obj):
    if isinstance(obj, dict):
        return hash(tuple((_compute_hash(k), _compute_hash(v))
                          for k, v in sorted(obj.items())))
    elif isinstance(obj, list):
        return hash(tuple(_compute_hash(i) for i in obj))
    else:
        return hash(obj)


class Base:
    __attrs__ = ()

    def __repr__(self):
        kwargs = ', '.join('{}={!r}'.format(attr, self.__dict__[attr])
                           for attr in self.__attrs__)
        return '{}({})'.format(self.__class__.__name__, kwargs)

    def __eq__(self, other):
        return (self.__class__ is other.__class__
                and all(self.__dict__[attr] == other.__dict__[attr]
                        for attr in self.__attrs__))

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self, **kwargs):
        obj = self.__class__.__new__(self.__class__)
        obj.__dict__.update((attr, kwargs.get(attr, self.__dict__[attr]))
                            for attr in self.__attrs__)
        return obj


class FieldBase(Base):

    @cached_property
    def result_key(self):
        if self.alias is not None:
            return self.alias
        else:
            return self.name

    @cached_property
    def options_hash(self):
        if self.options:
            return _compute_hash(self.options)
        else:
            return None

    @cached_property
    def index_key(self):
        if self.options_hash is not None:
            return '{}[{}]'.format(self.name, self.options_hash)
        else:
            return self.name


class Field(FieldBase):
    """Represents a field of the node

    :param name: name of the field
    :param optional options: field options -- mapping of names to values
    :param optional alias: field's name in result
    """
    __attrs__ = ('name', 'options', 'alias')

    def __init__(self, name, options=None, alias=None):
        self.name = name
        self.options = options
        self.alias = alias

    def accept(self, visitor):
        return visitor.visit_field(self)


class Link(FieldBase):
    """Represents a link to the node

    :param name: name of the link
    :param node: collection of fields and links --
                 :py:class:`~hiku.query.Node`
    :param optional options: link options -- mapping of names to values
    :param optional alias: link's name in result
    """
    __attrs__ = ('name', 'node', 'options', 'alias')

    def __init__(self, name, node, options=None, alias=None):
        self.name = name
        self.node = node
        self.options = options
        self.alias = alias

    def accept(self, visitor):
        return visitor.visit_link(self)


class Node(Base):
    """Represents collection of fields and links

    :param fields: list of :py:class:`~hiku.query.Field` and
        :py:class:`~hiku.query.Link`
    :param ordered: whether to compute fields of this node sequentially
        in order or not
    """
    __attrs__ = ('fields', 'ordered')

    def __init__(self, fields, ordered=False):
        self.fields = fields
        self.ordered = ordered

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    @cached_property
    def result_map(self):
        return OrderedDict((f.result_key, f) for f in self.fields)

    def accept(self, visitor):
        return visitor.visit_node(self)


def _merge(nodes):
    fields = set()
    links = {}
    to_merge = OrderedDict()
    for field in chain.from_iterable(e.fields for e in nodes):
        key = (field.name, field.options_hash, field.alias)
        if field.__class__ is Link:
            if key not in to_merge:
                to_merge[key] = [field.node]
                links[key] = field
            else:
                to_merge[key].append(field.node)
        else:
            if key not in fields:
                fields.add(key)
                yield field
    for key, values in to_merge.items():
        link = links[key]
        yield link.copy(node=merge(values))


def merge(nodes):
    """Merges multiple queries into one query

    :param nodes: queries, represented as list of :py:class:`~hiku.query.Node`
    :return: merged query as one :py:class:`~hiku.query.Node`
    """
    assert isinstance(nodes, Sequence), type(nodes)
    ordered = any(n.ordered for n in nodes)
    return Node(list(_merge(nodes)), ordered=ordered)


class QueryVisitor:

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        pass

    def visit_link(self, obj):
        self.visit(obj.node)

    def visit_node(self, obj):
        for item in obj.fields:
            self.visit(item)


class QueryTransformer:

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        return obj.copy()

    def visit_link(self, obj):
        return obj.copy(node=self.visit(obj.node))

    def visit_node(self, obj):
        return obj.copy(fields=[self.visit(f) for f in obj.fields])
