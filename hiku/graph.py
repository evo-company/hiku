"""
    hiku.graph
    ~~~~~~~~~~

    Graphs are defined by nodes, fields and links. Simple functions
    are used to fetch any data from any data source.

"""
import typing as t

from abc import ABC, abstractmethod
from itertools import chain
from functools import reduce
from collections import OrderedDict
from typing import List

from .types import (
    OptionalMeta,
    SequenceMeta,
    TypeRefMeta,
    Record,
    Any,
    GenericMeta,
)
from .utils import cached_property, const


Maybe = const('Maybe')

One = const('One')

Many = const('Many')

#: Special constant that is used by links with :py:class:`~hiku.types.Optional`
#: type in order to indicate that there is nothing to link to
Nothing = const('Nothing')


class AbstractBase(ABC):

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
    def __init__(
        self,
        name: str,
        type_: GenericMeta,
        *,
        default: t.Any = Nothing,
        description: t.Optional[str] = None
    ):
        """
        :param name: name of the option
        :param type_: type of the option or ``None``
        :param default: default option value
        :param description: description of the option
        """
        self.name = name
        self.type = type_
        self.default = default
        self.description = description

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

    Example with directives::

        graph = Graph([
            Root([
                Field('lorem-ipsum', String, func,
                      options=[Option('words', Integer, default=50)],
                      directives=[Deprecated('use another field')]),
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
    def __init__(self, name, type_, func, *, options=None, description=None,
                 directives=None):
        """
        :param str name: name of the field
        :param type_: type of the field or ``None``
        :param func: function to load field's data
        :param options: list of acceptable options
        :param description: description of the field
        :param directives: list of directives for the field
        """
        self.name = name
        self.type = type_
        self.func = func
        self.options = options or ()
        self.description = description
        self.directives = directives or ()

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

    Example with directives::

        graph = Graph([
            Node('user', [...]),
            Root([
                Link('users', Sequence[TypeRef['user']], func, requires=None,
                     options=[Option('limit', Integer, default=100)],
                     directives=[Deprecated('do not use')]),
            ]),
        ])

    Identifiers loading function protocol::

        # From root node or if requires is None:

        # ... if type is TypeRef['foo']
        def func() -> T

        # ... if type is Optional[TypeRef['foo']]
        def func() -> Union[T, Nothing]

        # ... if type is Sequence[TypeRef['foo']]
        def func() -> List[T]

        # From non-root node and requires is not None:

        # ... if type is TypeRef['foo']
        def func(ids) -> List[T]

        # ... if type is Optional[TypeRef['foo']]
        def func(ids) -> List[Union[T, Nothing]]

        # ... if type is Sequence[TypeRef['foo']]
        def func(ids) -> List[List[T]]

    See also :py:const:`hiku.graph.Nothing`.

    If link was defined with options, then link function should accept one
    additional positional argument::

        # many to many link with options
        def func(ids, options) -> List[List[T]]

    Where ``options`` is a mapping ``str: value`` of provided in the query
    options.
    """
    def __init__(
        self, name, type_, func, *, requires, options=None, description=None,
        directives=None
    ):
        """
        :param name: name of the link
        :param type_: type of the link
        :param func: function to load identifiers of the linked node
        :param requires: field name from the current node, required to compute
                         identifiers of the linked node
        :param options: list of acceptable options
        :param description: description of the link
        :param directives: list of directives for the link
        """
        type_enum, node = get_type_enum(type_)

        self.name = name
        self.type = type_
        self.type_enum = type_enum
        self.node = node
        self.func = func
        self.requires = requires
        self.options = options or ()
        self.description = description
        self.directives = directives or ()

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
    def __init__(self, name, fields, *, description=None, directives=None):
        """
        :param name: name of the node
        :param fields: list of fields and links
        :param description: description of the node
        """
        self.name = name
        self.fields = fields
        self.description = description
        self.directives = directives or ()

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
    def __init__(self, items, data_types=None):
        """
        :param items: list of nodes
        """
        from .validate.graph import GraphValidator

        GraphValidator.validate(items)

        self.items = GraphInit.init(items)
        self.data_types = data_types or {}
        self.__types__ = GraphTypes.get_types(self.items, self.data_types)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.items)

    def iter_root(self):
        for node in self.items:
            if node.name is None:
                for field in node.fields:
                    yield field

    def iter_nodes(self):
        for node in self.items:
            if node.name is not None:
                yield node

    @cached_property
    def root(self):
        return Root(list(self.iter_root()))

    @cached_property
    def nodes(self):
        return list(self.iter_nodes())

    @cached_property
    def nodes_map(self):
        return OrderedDict((e.name, e) for e in self.iter_nodes())

    def accept(self, visitor):
        return visitor.visit_graph(self)


class AbstractGraphVisitor(ABC):

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
        return Option(obj.name, obj.type, default=obj.default,
                      description=obj.description)

    def visit_field(self, obj):
        return Field(obj.name, obj.type, obj.func,
                     options=[self.visit(op) for op in obj.options],
                     description=obj.description, directives=obj.directives)

    def visit_link(self, obj):
        return Link(obj.name, obj.type, obj.func,
                    requires=obj.requires,
                    options=[self.visit(op) for op in obj.options],
                    description=obj.description, directives=obj.directives)

    def visit_node(self, obj):
        return Node(obj.name, [self.visit(f) for f in obj.fields],
                    description=obj.description, directives=obj.directives)

    def visit_root(self, obj):
        return Root([self.visit(f) for f in obj.fields])

    def visit_graph(self, obj):
        return Graph([self.visit(node) for node in obj.items],
                     obj.data_types)


def apply(graph: Graph, transformers: List[GraphTransformer]) -> Graph:
    """Helper function to apply graph transformations

    Example:

    .. code-block:: python

        graph = hiku.graph.apply(graph, [AsyncGraphQLIntrospection()])

    """
    return reduce(lambda g, t: t.visit(g), transformers, graph)


class GraphInit(GraphTransformer):

    @classmethod
    def init(cls, items):
        self = cls()
        return [self.visit(i) for i in items]

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


class GraphTypes(GraphVisitor):

    def _visit_graph(self, items, data_types):
        types = OrderedDict(data_types)
        roots = []
        for item in items:
            if item.name is not None:
                types[item.name] = self.visit(item)
            else:
                roots.append(self.visit(item))
        types['__root__'] = Record[chain.from_iterable(
            r.__field_types__.items() for r in roots
        )]
        return types

    @classmethod
    def get_types(cls, items, data_types):
        return cls()._visit_graph(items, data_types)

    def visit_graph(self, obj):
        return self._visit_graph(obj.items, obj.data_types)

    def visit_node(self, obj):
        return Record[[(f.name, self.visit(f)) for f in obj.fields]]

    def visit_root(self, obj):
        return Record[[(f.name, self.visit(f)) for f in obj.fields]]

    def visit_link(self, obj):
        return obj.type

    def visit_field(self, obj):
        return obj.type or Any
