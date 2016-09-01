"""
hiku.graph
==========

Graph is defined by edges, fields and links. Simple functions
are used to fetch any data from any source.
"""
from abc import ABCMeta, abstractmethod
from itertools import chain
from collections import OrderedDict

from .utils import kw_only, cached_property, const
from .compat import with_metaclass


Maybe = const('Maybe')
One = const('One')
Many = const('Many')

Nothing = const('Nothing')


class AbstractNode(with_metaclass(ABCMeta)):

    @abstractmethod
    def accept(self, visitor):
        pass


class AbstractOption(AbstractNode):
    pass


class Option(AbstractOption):
    """
    *class* ``hiku.graph.Option(name, type, *, default=None)``

    *class* ``hiku.graph.Option(name, *, default=None)``

    Options are also optionally typed, so there are also two class signatures.

    - ``name: str`` - name of the option
    - ``type: hiku.types.GenericMeta`` - type of the option
    - ``default: Any`` - default option value
    """
    def __init__(self, name, *other, **kwargs):
        if not len(other):
            type_ = None
        elif len(other) == 1:
            type_, = other
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other) + 1))

        self.name = name
        self.type = type_
        self.default, = kw_only(kwargs, [], ['default'])

    def accept(self, visitor):
        return visitor.visit_option(self)


class AbstractField(AbstractNode):
    pass


class Field(AbstractField):
    """
    *class* ``hiku.graph.Field(name, type, func, *, options=None,
    description=None)``

    *class* ``hiku.graph.Field(name, func, *, options=None, description=None)``

    Typing is optional, so there are two class signatures.

    - ``name: str`` - name of the field
    - ``type: hiku.types.GenericMeta`` - type of the field
    - ``func: Union[Callable, Coroutine]`` - function to resolve field values
    - ``options: Optional[Sequence[hiku.graph.Option]]``
    - ``description: Optional[str]`` - field description

    Field function's protocol:

    .. code-block:: python

      def fields_func(fields: Sequence[hiku.query.Field]) -> Sequence[Any]:
          \"""Resolves field values in the root edge\"""

      def fields_func(fields: Sequence[hiku.query.Field], ids: Sequence[ID])
          -> Sequence[Sequence[Any]]:
          \"""Resolves field values in regular edges\"""
    """
    def __init__(self, name, *other, **kwargs):
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            type_, func = None, other[0]
        elif len(other) == 2:
            type_, func = other
        else:
            raise TypeError('More positional arguments ({}) than expected (3)'
                            .format(len(other) + 1))

        options, description = kw_only(kwargs, [], ['options', 'description'])

        self.name = name
        self.type = type_
        self.func = func
        self.options = options or ()
        self.description = description

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class AbstractLink(AbstractNode):
    pass


class Link(AbstractLink):
    """
    *class* ``hiku.graph.Link(name, type, func, *, edge, requires, options=None,
    description=None)``

    Links are used to point to other edges.

    - ``name: str`` - name of the link
    - ``type: Union[hiku.graph.Maybe, hiku.graph.One, hiku.graph.Many]``
    - ``func: Union[Callable, Coroutine]`` - function to resolve linked edge ids
    - ``edge: str`` - name of the linked edge
    - ``requires: Optional[str]`` - field name, which is used to associate this
      edge with linked edge
    - ``options: Optional[Sequence[hiku.graph.Option]]`` - list of accepted
      options
    - ``description: Optional[str]`` - link description

    Link types:

    - ``hiku.graph.Maybe`` - one or nothing
    - ``hiku.graph.One`` - exactly one
    - ``hiku.graph.Many`` - sequence

    Link function's protocol:

    .. code-block:: python

      ID = Hashable
      MaybeID = Union[ID, hiku.graph.Nothing]

      def link_func() -> MaybeID:
          \"""Link to maybe one\"""

      def link_func() -> ID:
          \"""Link to one\"""

      def link_func() -> Sequence[ID]:
          \"""Link to many\"""

      def link_func(ids: Sequence[ID]) -> Sequence[MaybeID]:
          \"""Link from one/many to maybe one\"""

      def link_func(ids: Sequence[ID]) -> Sequence[ID]:
          \"""Link from one/many to one\"""

      def link_func(ids: Sequence[ID]) -> Sequence[Sequence[ID]]:
          \"""Link from one/many to many\"""

    If link was defined with options, then link function should accept another
    one positional parameter: ``Mapping[str, Any]`` - provided in query link
    values, for example:

    .. code-block:: python

      def link_func(options: Mapping[str, Any]) -> Sequence[ID]:
          \"""Link to many with options\"""

      def link_func(ids: Sequence[ID], options: Mapping[str, Any]) \\
          -> Sequence[ID]:
          \"""Link from one/many to one with options\"""
    """
    def __init__(self, name, type_, func, **kwargs):
        edge, requires, options, description = \
            kw_only(kwargs, ['edge', 'requires'], ['options', 'description'])

        self.name = name
        self.type = type_
        self.func = func
        self.edge = edge
        self.requires = requires
        self.options = options or ()
        self.description = description

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_link(self)


class AbstractEdge(AbstractNode):
    pass


class Edge(AbstractEdge):
    """
    Collection of the fields and links, which describes some entity and
    relations with other entities.

    *class* ``hiku.graph.Edge(name, fields, *, description=None)``

    - ``name: str`` - name of the edge
    - ``fields: Sequence[Union[hiku.graph.Field, hiku.graph.Link]]``
    - ``description: Optional[str]`` - edge description
    """
    def __init__(self, name, fields, **kwargs):
        self.name = name
        self.fields = fields
        self.description, = kw_only(kwargs, [], ['description'])

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor):
        return visitor.visit_edge(self)


class Root(Edge):
    """
    Special implicit edge, where query execution starts from.

    *class* ``hiku.graph.Root(items)``

    - ``items: Sequence[Union[hiku.graph.Edge, hiku.graph.Field,
      hiku.graph.Link]]``
    """
    def __init__(self, items):
        super(Root, self).__init__(None, items)


class AbstractGraph(AbstractNode):
    pass


class Graph(AbstractGraph):
    """Collection of edges - definition of the graph

    *class* ``hiku.graph.Graph(items)``

    - ``items: Sequence[hiku.graph.Edge]`` - list of edges
    """
    def __init__(self, items):
        self.items = items

    @cached_property
    def root(self):
        return Root(list(chain.from_iterable(e.fields for e in self.items
                                             if e.name is None)))

    @cached_property
    def edges(self):
        return [e for e in self.items if e.name is not None]

    @cached_property
    def edges_map(self):
        return OrderedDict((e.name, e) for e in self.edges)

    def accept(self, visitor):
        return visitor.visit_graph(self)


class GraphVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_option(self, obj):
        pass

    def visit_field(self, obj):
        for option in obj.options:
            self.visit(option)

    def visit_link(self, obj):
        for option in obj.options:
            self.visit(option)

    def visit_edge(self, obj):
        for item in obj.fields:
            self.visit(item)

    def visit_graph(self, obj):
        for item in obj.items:
            self.visit(item)
