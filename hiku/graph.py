"""
    hiku.graph
    ~~~~~~~~~~

    Graphs are defined by nodes, fields and links. Simple functions
    are used to fetch any data from any data source.

"""
from abc import ABCMeta, abstractmethod
from functools import reduce
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


class AbstractBase(with_metaclass(ABCMeta)):

    @abstractmethod
    def accept(self, visitor):
        pass


class AbstractOption(AbstractBase):
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
        self.default, = kw_only(self.__init__, kwargs, [],
                                [('default', Nothing)])

    def __repr__(self):
        return '{}({!r}, {!r}, ...)'.format(self.__class__.__name__,
                                            self.name, self.type)

    def accept(self, visitor):
        return visitor.visit_option(self)


class AbstractField(AbstractBase):
    pass


class Field(AbstractField):
    """Defines a field of the node

    Example::

        graph = Graph([
            Node('user', [
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

        # root node fields
        def func(fields) -> List[T]

        # non-root node fields
        def func(fields, ids) -> List[List[T]]

    Where:

    - ``fields`` - list of :py:class:`hiku.query.Field`
    - ``ids`` - list node identifiers

    """
    def __init__(self, name, type_, func, **kwargs):
        """
        :param str name: name of the field
        :param type_: type of the field or ``None``
        :param func: function to load field's data
        :param kw-only,optional options: list of acceptable options
        :param kw-only,optional description: description of the field
        """
        options, description = kw_only(self.__init__, kwargs, [],
                                       [('options', None),
                                        ('description', None)])

        self.name = name
        self.type = type_
        self.func = func
        self.options = options or ()
        self.description = description

    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(self.__class__.__name__, self.name,
                                             self.type, self.func)

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class AbstractLink(AbstractBase):
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
    """Defines a link to the node

    Example::

        graph = Graph([
            Node('user', [...]),
            Root([
                Link('users', Sequence[TypeRef['user']], func, requires=None),
            ]),
        ])

    Example with requirements::

        graph = Graph([
            Node('character', [...]),
            Node('actor', [
                Field('id', Integer, field_func),
                Link('characters', Sequence[TypeRef['character']],
                     link_func, requires='id'),
            ])
        ])

    Requirements are needed when link points from non-root node.

    Example with options::

        graph = Graph([
            Node('user', [...]),
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
        :param func: function to load identifiers of the linked node
        :param kw-only requires: field name from the current node, required
                                      to compute identifiers of the linked node
        :param kw-only,optional options: list of acceptable options
        :param kw-only,optional description: description of the link
        """
        requires, options, description = \
            kw_only(self.__init__, kwargs, ['requires'],
                    [('options', None), ('description', None)])

        type_enum, node = get_type_enum(type_)

        self.name = name
        self.type = type_
        self.type_enum = type_enum
        self.node = node
        self.func = func
        self.requires = requires
        self.options = options or ()
        self.description = description

    def __repr__(self):
        return '{}({!r}, {!r}, {!r}, ...)'.format(self.__class__.__name__,
                                                  self.name, self.type,
                                                  self.func)

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_link(self)


class AbstractNode(AbstractBase):
    pass


class Node(AbstractNode):
    """Collection of the fields and links, which describes some entity and
    relations with other entities

    Example::

        graph = Graph([
            Node('user', [
                Field('id', Integer, field_func),
                Field('name', String, field_func),
                Link('roles', Sequence[TypeRef['role']],
                     link_func, requires='id'),
            ]),
        ])

    """
    def __init__(self, name, fields, **kwargs):
        """
        :param name: name of the node
        :param fields: list of fields and links
        :param kw-only,optional description: description of the node
        """
        self.name = name
        self.fields = fields
        self.description, = kw_only(self.__init__, kwargs, [],
                                    [('description', None)])

    def __repr__(self):
        return '{}({!r}, {!r}, ...)'.format(self.__class__.__name__, self.name,
                                            self.fields)

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor):
        return visitor.visit_node(self)


class Root(Node):
    """Special implicit root node, starting point of the query execution

    Example::

        graph = Graph([
            Node('baz', [...]),
            Root([
                Field('foo', String, root_fields_func),
                Link('bar', Sequence[TypeRef['baz']],
                     to_baz_func, requires=None),
                Node('quux', [...]),
            ]),
        ])

    """
    def __init__(self, items):
        """
        :param items: list of fields, links and singleton nodes
        """
        super(Root, self).__init__(None, items)

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__, self.name,
                                       self.fields)

    def accept(self, visitor):
        return visitor.visit_root(self)


class AbstractGraph(AbstractBase):
    pass


class Graph(AbstractGraph):
    """Collection of nodes - definition of the graph

    Example::

        graph = Graph([
            Node('foo', [...]),
            Node('bar', [...]),
            Root([...]),
        ])

    """
    def __init__(self, items):
        """
        :param items: list of nodes
        """
        from .validate.graph import GraphValidator

        GraphValidator.validate(items)

        self.items = GraphInit.init(items)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.items)

    @cached_property
    def root(self):
        return Root(list(chain.from_iterable(e.fields for e in self.items
                                             if e.name is None)))

    @cached_property
    def nodes(self):
        return [e for e in self.items if e.name is not None]

    @cached_property
    def nodes_map(self):
        return OrderedDict((e.name, e) for e in self.nodes)

    def accept(self, visitor):
        return visitor.visit_graph(self)


class AbstractGraphVisitor(with_metaclass(ABCMeta, object)):

    @abstractmethod
    def visit(self, obj):
        pass

    @abstractmethod
    def visit_option(self, obj):
        pass

    @abstractmethod
    def visit_field(self, obj):
        pass

    @abstractmethod
    def visit_link(self, obj):
        pass

    @abstractmethod
    def visit_node(self, obj):
        pass

    @abstractmethod
    def visit_root(self, obj):
        pass

    @abstractmethod
    def visit_graph(self, obj):
        pass


class GraphVisitor(AbstractGraphVisitor):

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

    def visit_node(self, obj):
        for item in obj.fields:
            self.visit(item)

    def visit_root(self, obj):
        for item in obj.fields:
            self.visit(item)

    def visit_graph(self, obj):
        for item in obj.items:
            self.visit(item)


class GraphTransformer(AbstractGraphVisitor):

    def visit(self, obj):
        return obj.accept(self)

    def visit_option(self, obj):
        return Option(obj.name, obj.type, default=obj.default)

    def visit_field(self, obj):
        return Field(obj.name, obj.type, obj.func,
                     options=[self.visit(op) for op in obj.options],
                     description=obj.description)

    def visit_link(self, obj):
        return Link(obj.name, obj.type, obj.func,
                    requires=obj.requires,
                    options=[self.visit(op) for op in obj.options],
                    description=obj.description)

    def visit_node(self, obj):
        return Node(obj.name, [self.visit(f) for f in obj.fields],
                    description=obj.description)

    def visit_root(self, obj):
        return Root([self.visit(f) for f in obj.fields])

    def visit_graph(self, obj):
        return Graph([self.visit(node) for node in obj.items])


def apply(graph, transformers):
    return reduce(lambda g, t: t.visit(g), transformers, graph)


class GraphInit(GraphTransformer):

    @classmethod
    def init(cls, items):
        graph_init = cls()
        return [graph_init.visit(i) for i in items]

    def visit_field(self, obj):
        field = super(GraphInit, self).visit_field(obj)
        postprocess = getattr(field.func, '__postprocess__', None)
        if postprocess is not None:
            postprocess(field)
        return field

    def visit_link(self, obj):
        link = super(GraphInit, self).visit_link(obj)
        postprocess = getattr(link.func, '__postprocess__', None)
        if postprocess is not None:
            postprocess(link)
        return link
