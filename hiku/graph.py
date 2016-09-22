"""
    hiku.graph
    ~~~~~~~~~~

    Graphs are defined by edges, fields and links. Simple functions
    are used to fetch any data from any data source.

"""
from abc import ABCMeta, abstractmethod
from itertools import chain
from collections import OrderedDict

from .types import OptionalMeta, SequenceMeta, TypeRefMeta
from .utils import kw_only, cached_property, const
from .compat import with_metaclass

Maybe = const('Maybe')

One = const('One')

Many = const('Many')

#: Special constant that is used by links with :py:class:`~hiku.types.Optional`
#: type in order to indicate that there is nothing to link to
Nothing = const('Nothing')


class AbstractNode(with_metaclass(ABCMeta)):

    @abstractmethod
    def accept(self, visitor):
        pass


class AbstractOption(AbstractNode):
    pass


class Option(AbstractOption):
    """Defines an option, used to customize results of the fields and links

    Options without default value are **required**.

    Example of a required option::

        Option('id', Integer)

    Example of an optional option::

        Option('size', Integer, default=100)

    """
    def __init__(self, name, type_, **kwargs):
        """
        :param name: name of the option
        :param type_: type of the option or ``None``
        :param kw-only,optional default: default option value
        """
        self.name = name
        self.type = type_
        self.default, = kw_only(kwargs, [], ['default'])

    def accept(self, visitor):
        return visitor.visit_option(self)


class AbstractField(AbstractNode):
    pass


class Field(AbstractField):
    """Defines a field of the edge

    Example::

        graph = Graph([
            Edge('user', [
                Field('name', String, func),
            ]),
        ])

    Example with options::

        graph = Graph([
            Root([
                Field('lorem-ipsum', String, func,
                      options=[Option('words', Integer, default=50)]),
            ]),
        ])

    Data loading protocol::

        # root edge fields
        def func(fields) -> List[T]

        # non-root edge fields
        def func(fields, ids) -> List[List[T]]

    Where:

    - ``fields`` - list of :py:class:`hiku.query.Field`
    - ``ids`` - list edge identifiers

    """
    def __init__(self, name, type_, func, **kwargs):
        """
        :param str name: name of the field
        :param type_: type of the field or ``None``
        :param func: function to load field's data
        :param kw-only,optional options: list of acceptable options
        :param kw-only,optional description: description of the field
        """
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


def get_type_enum(type_):
    if isinstance(type_, TypeRefMeta):
        return One, type_.__type_name__
    elif isinstance(type_, OptionalMeta):
        if isinstance(type_.__type__, TypeRefMeta):
            return Maybe, type_.__type__.__type_name__
    elif isinstance(type_, SequenceMeta):
        if isinstance(type_.__item_type__, TypeRefMeta):
            return Many, type_.__item_type__.__type_name__
    raise TypeError('Invalid type specified: {!r}'.format(type_))


class Link(AbstractLink):
    """Defines a link to the edge

    Example::

        graph = Graph([
            Edge('user', [...]),
            Root([
                Link('users', Sequence[TypeRef['user']], func, requires=None),
            ]),
        ])

    Example with requirements::

        graph = Graph([
            Edge('character', [...]),
            Edge('actor', [
                Field('id', Integer, field_func),
                Link('characters', Sequence[TypeRef['character']],
                     link_func, requires='id'),
            ])
        ])

    Requirements are needed when link points from non-root edge.

    Example with options::

        graph = Graph([
            Edge('user', [...]),
            Root([
                Link('users', Sequence[TypeRef['user']], func, requires=None,
                     options=[Option('limit', Integer, default=100)]),
            ]),
        ])

    Identifiers loading function protocol::

        # requires is None and type is TypeRef['foo']
        def func() -> T

        # requires is None and type is Optional[TypeRef['foo']]
        def func() -> Union[T, Nothing]

        # requires is None and type is Sequence[TypeRef['foo']]
        def func() -> List[T]

        # requires is not None and type is TypeRef['foo']
        def func(ids) -> List[T]

        # requires is not None and type is Optional[TypeRef['foo']]
        def func(ids) -> List[Union[T, Nothing]]

        # requires is not None and type is Sequence[TypeRef['foo']]
        def func(ids) -> List[List[T]]

    See also :py:const:`hiku.graph.Nothing`.

    If link was defined with options, then link function should accept one
    additional positional argument::

        # many to many link with options
        def func(ids, options) -> List[List[T]]

    Where ``options`` is a mapping ``str: value`` of provided in the query
    options.
    """
    def __init__(self, name, type_, func, **kwargs):
        """
        :param name: name of the link
        :param type_: type of the link
        :param func: function to load identifiers of the linked edge
        :param kw-only edge: name of the linked edge
        :param kw-only requires: field name from the current edge, required
                                      to compute identifiers of the linked edge
        :param kw-only,optional options: list of acceptable options
        :param kw-only,optional description: description of the link
        """
        requires, options, description = \
            kw_only(kwargs, ['requires'], ['options', 'description'])

        type_enum, edge = get_type_enum(type_)

        self.name = name
        self.type = type_
        self.type_enum = type_enum
        self.edge = edge
        self.func = func
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
    """Collection of the fields and links, which describes some entity and
    relations with other entities

    Example::

        graph = Graph([
            Edge('user', [
                Field('id', Integer, field_func),
                Field('name', String, field_func),
                Link('roles', Sequence[TypeRef['role']],
                     link_func, requires='id'),
            ]),
        ])

    """
    def __init__(self, name, fields, **kwargs):
        """
        :param name: name of the edge
        :param fields: list of fields and links
        :param kw-only,optional description: description of the edge
        """
        self.name = name
        self.fields = fields
        self.description, = kw_only(kwargs, [], ['description'])

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor):
        return visitor.visit_edge(self)


class Root(Edge):
    """Special implicit root edge, starting point of the query execution

    Example::

        graph = Graph([
            Edge('baz', [...]),
            Root([
                Field('foo', String, root_fields_func),
                Link('bar', Sequence[TypeRef['baz']],
                     to_baz_func, requires=None),
                Edge('quux', [...]),
            ]),
        ])

    """
    def __init__(self, items):
        """
        :param items: list of fields, links and singleton edges
        """
        super(Root, self).__init__(None, items)


class AbstractGraph(AbstractNode):
    pass


class Graph(AbstractGraph):
    """Collection of edges - definition of the graph

    Example::

        graph = Graph([
            Edge('foo', [...]),
            Edge('bar', [...]),
            Root([...]),
        ])

    """
    def __init__(self, items):
        """
        :param items: list of edges
        """
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
