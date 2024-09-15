"""
hiku.query
~~~~~~~~~~

`Hiku` doesn't rely on any specific query language, internally it uses
generic query representation to describe result and it could be constructed
by parsing different suitable query languages.

However, `Hiku` provides built-in way to parse graphql
query into `hiku.query.Node`:

Example:

.. code-block:: graphql

    { foo { bar { baz } } }

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
"""

import typing as t
import hashlib

from functools import cached_property
from itertools import chain
from collections import (
    OrderedDict,
    defaultdict,
)
from collections.abc import Sequence

from .directives import Directive
from .compat import TypeAlias


T = t.TypeVar("T", bound="Base")


def _compute_hash(obj: t.Any) -> int:
    if isinstance(obj, dict):
        return hash(
            tuple(
                (_compute_hash(k), _compute_hash(v))
                for k, v in sorted(obj.items())
            )
        )
    if isinstance(obj, list):
        return hash(tuple(_compute_hash(i) for i in obj))
    if isinstance(obj, bytes):
        return int(hashlib.sha1(obj).hexdigest(), 16)
    if isinstance(obj, str):
        return int(hashlib.sha1(obj.encode("utf-8")).hexdigest(), 16)
    return hash(obj)


class Base:
    __attrs__: t.Tuple[str, ...] = ()

    def __repr__(self) -> str:
        kwargs = ", ".join(
            "{}={!r}".format(attr, self.__dict__[attr])
            for attr in self.__attrs__
        )
        return "{}({})".format(self.__class__.__name__, kwargs)

    def __eq__(self, other: t.Any) -> bool:
        return self.__class__ is other.__class__ and all(
            self.__dict__[attr] == other.__dict__[attr]
            for attr in self.__attrs__
        )

    def __ne__(self, other: t.Any) -> bool:
        return not self.__eq__(other)

    def copy(self: T, **kwargs: t.Any) -> T:
        obj = self.__class__.__new__(self.__class__)
        obj.__dict__.update(
            (attr, kwargs.get(attr, self.__dict__[attr]))
            for attr in self.__attrs__
        )
        return obj


class FieldBase(Base):
    name: str
    options: t.Optional[t.Dict[str, t.Any]]
    alias: t.Optional[str]

    @cached_property
    def result_key(self) -> str:
        if self.alias is not None:
            return self.alias
        else:
            return self.name

    @cached_property
    def options_hash(self) -> t.Optional[int]:
        if self.options:
            return _compute_hash(self.options)
        else:
            return None

    @cached_property
    def index_key(self) -> str:
        if self.options_hash is not None:
            return "{}[{}]".format(self.name, self.options_hash)
        else:
            return self.name

    def __hash__(self) -> int:
        return hash(self.index_key)


class Field(FieldBase):
    """Represents a field of the node

    :param name: name of the field
    :param optional options: field options -- mapping of names to values
    :param optional alias: field's name in result
    """

    __attrs__ = ("name", "options", "alias", "directives")

    def __init__(
        self,
        name: str,
        options: t.Optional[t.Dict[str, t.Any]] = None,
        alias: t.Optional[str] = None,
        directives: t.Optional[t.Tuple[Directive, ...]] = None,
    ):
        self.name = name
        self.options = options
        self.alias = alias
        self.directives = directives or ()

    @cached_property
    def directives_map(self) -> OrderedDict:
        directives = OrderedDict()
        for d in self.directives:
            if d.__directive_info__.name not in directives:
                directives[d.__directive_info__.name] = d
        return directives

    def accept(self, visitor: "QueryVisitor") -> t.Any:
        return visitor.visit_field(self)


class Link(FieldBase):
    """Represents a link to the node

    :param name: name of the link
    :param node: collection of fields and links --
                 :py:class:`~hiku.query.Node`
    :param optional options: link options -- mapping of names to values
    :param optional alias: link's name in result
    """

    __attrs__ = (
        "name",
        "node",
        "options",
        "alias",
        "directives",
    )

    def __init__(
        self,
        name: str,
        node: "Node",
        options: t.Optional[t.Dict[str, t.Any]] = None,
        alias: t.Optional[str] = None,
        directives: t.Optional[t.Tuple[Directive, ...]] = None,
    ):
        self.name = name
        self.node = node
        self.options = options
        self.alias = alias
        self.directives = directives or ()

    @cached_property
    def directives_map(self) -> OrderedDict:
        directives = OrderedDict()
        for d in self.directives:
            if d.__directive_info__.name not in directives:
                directives[d.__directive_info__.name] = d
        return directives

    def accept(self, visitor: "QueryVisitor") -> t.Any:
        return visitor.visit_link(self)


FieldOrLink: TypeAlias = t.Union[Field, Link]
FieldsMap: TypeAlias = "OrderedDict[str, FieldOrLink]"
FragmentMap: TypeAlias = "OrderedDict[str, Fragment]"


class Node(Base):
    """Represents collection of fields, links and fragments

    :param fields: list of :py:class:`~hiku.query.Field`,
        :py:class:`~hiku.query.Link`, :py:class:`~hiku.query.Fragment`
    :param fragments: list of :py:class:`~hiku.query.Fragment`
    :param ordered: whether to compute fields of this node sequentially
        in order or not
    """

    __attrs__ = ("fields", "fragments", "ordered")

    def __init__(
        self,
        fields: t.Sequence[FieldOrLink],
        fragments: t.Optional[t.Sequence["Fragment"]] = None,
        ordered: bool = False,
    ) -> None:
        self.fields = list(fields)
        self.fragments = list(fragments or [])
        self.ordered = ordered

    @cached_property
    def fields_map(
        self,
    ) -> FieldsMap:
        return OrderedDict((f.name, f) for f in self.fields)

    @cached_property
    def fragments_map(self) -> FragmentMap:
        """Only named fragments"""
        return OrderedDict(
            (f.name, f) for f in self.fragments if f.name is not None
        )

    @cached_property
    def result_map(self) -> OrderedDict:
        return OrderedDict((f.result_key, f) for f in self.fields)

    def accept(self, visitor: "QueryVisitor") -> t.Any:
        return visitor.visit_node(self)

    def __hash__(self) -> int:
        return hash(tuple(self.fields)) + hash(tuple(self.fragments))


class Fragment(Base):
    __attrs__ = ("name", "type_name", "node")

    def __init__(
        self,
        name: t.Optional[str],
        type_name: t.Optional[str],
        node: Node,
    ) -> None:
        self.name = name  # if None, it's an inline fragment
        self.type_name = type_name
        self.node = node

    def accept(self, visitor: "QueryVisitor") -> t.Any:
        return visitor.visit_fragment(self)

    def __hash__(self) -> int:
        return hash(self.type_name) + hash(self.node)


KeyT = t.Tuple[str, t.Optional[int], t.Optional[str]]


def field_key(field: FieldOrLink) -> KeyT:
    return (field.name, field.options_hash, field.alias)


def _merge(
    nodes: t.Iterable[Node],
) -> t.Iterator[t.Union[FieldOrLink, Fragment]]:
    visited_fields = set()
    links = {}
    link_directives: t.DefaultDict[t.Tuple, t.List] = defaultdict(list)
    to_merge = OrderedDict()
    fields_iter = chain.from_iterable(e.fields for e in nodes)
    fragments_iter = chain.from_iterable(e.fragments for e in nodes)

    for field in fields_iter:
        key = field_key(field)

        if field.__class__ is Link:
            field = t.cast(Link, field)
            if key not in to_merge:
                to_merge[key] = [field.node]
                links[key] = field
            else:
                to_merge[key].append(field.node)
            link_directives[key].extend(field.directives)
        else:
            if key not in visited_fields:
                visited_fields.add(key)
                yield field

    for fr in fragments_iter:
        yield fr

    for key, values in to_merge.items():
        link = links[key]
        directives = link_directives[key]
        yield link.copy(node=merge(values), directives=tuple(directives))


def merge(nodes: t.Iterable[Node]) -> Node:
    """Merges multiple queries into one query

    :param nodes: queries, represented as list of :py:class:`~hiku.query.Node`
    :return: merged query as one :py:class:`~hiku.query.Node`
    """
    assert isinstance(nodes, Sequence), type(nodes)
    ordered = any(n.ordered for n in nodes)
    fields = []
    fragments = []
    for item in _merge(nodes):
        if isinstance(item, Fragment):
            fragments.append(item)
        else:
            fields.append(item)

    return Node(fields=fields, fragments=fragments, ordered=ordered)


class QueryVisitor:
    def visit(self, obj: t.Any) -> t.Any:
        return obj.accept(self)

    def visit_field(self, obj: Field) -> t.Any:
        pass

    def visit_link(self, obj: Link) -> t.Any:
        self.visit(obj.node)

    def visit_node(self, obj: Node) -> t.Any:
        for item in obj.fields:
            self.visit(item)

    def visit_fragment(self, obj: Fragment) -> t.Any:
        self.visit(obj.node)


class QueryTransformer:
    def visit(self, obj: t.Any) -> t.Any:
        return obj.accept(self)

    def visit_field(self, obj: Field) -> Field:
        return obj.copy()

    def visit_link(self, obj: Link) -> Link:
        return obj.copy(node=self.visit(obj.node))

    def visit_node(self, obj: Node) -> Node:
        return obj.copy(fields=[self.visit(f) for f in obj.fields])

    def visit_fragment(self, obj: Fragment) -> Fragment:
        return obj.copy(node=self.visit(obj.node))
