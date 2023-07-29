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
from collections import OrderedDict, defaultdict
from typing import List

from .types import (
    InterfaceRef,
    InterfaceRefMeta,
    Optional,
    OptionalMeta,
    RefMeta,
    Sequence,
    SequenceMeta,
    TypeRef,
    Record,
    Any,
    GenericMeta,
    TypingMeta,
    AnyMeta,
    UnionRef,
    UnionRefMeta,
)
from .utils import (
    cached_property,
    const,
    Const,
)
from .directives import SchemaDirective

from .compat import TypeAlias


if t.TYPE_CHECKING:
    from .sources.graph import SubGraph
    from .sources.graph import BoundExpr

# TODO enum ???
Maybe = const("Maybe")

One = const("One")

Many = const("Many")

MaybeMany = const("MaybeMany")

#: Special constant that is used by links with :py:class:`~hiku.types.Optional`
#: type in order to indicate that there is nothing to link to
Nothing = const("Nothing")
NothingType: TypeAlias = Const


class AbstractBase(ABC):
    @abstractmethod
    def accept(self, visitor: "AbstractGraphVisitor") -> None:
        pass


class AbstractOption(AbstractBase, ABC):
    pass


class Option(AbstractOption):
    """Defines an option, used to customize results of the fields and links

    Options without default value are **required**.

    Example of a required option::

        Option('id', Integer)

    Example of an optional option::

        Option('size', Integer, default=100)

    Example with TypeRef type(ref can point either to Node or data type)::

        Option('filter', TypeRef['FilterInput'])

    """

    def __init__(
        self,
        name: str,
        type_: t.Optional[GenericMeta],
        *,
        default: t.Any = Nothing,
        description: t.Optional[str] = None,
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

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, ...)".format(
            self.__class__.__name__, self.name, self.type
        )

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_option(self)


class AbstractField(AbstractBase, ABC):
    pass


R = t.TypeVar("R")

SyncAsync = t.Union[R, t.Awaitable[R]]

# (fields) -> []
RootFieldFunc = t.Callable[[t.List["Field"]], SyncAsync[List[t.Any]]]
# (fields, ids) -> [[]]
NotRootFieldFunc = t.Callable[
    [t.List["Field"], List[t.Any]], SyncAsync[List[List[t.Any]]]
]
# (ctx, fields, ids) -> [[]]
NotRootFieldFuncCtx = t.Callable[
    [t.Any, t.List["Field"], List[t.Any]], SyncAsync[List[List[t.Any]]]
]


FieldType = t.Optional[GenericMeta]
FieldFunc = t.Union[
    RootFieldFunc,
    NotRootFieldFunc,
    NotRootFieldFuncCtx,
    "SubGraph",
    "BoundExpr",
]


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

    def __init__(
        self,
        name: str,
        type_: FieldType,
        func: FieldFunc,
        *,
        options: t.Optional[t.Sequence[Option]] = None,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
    ):
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

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, {!r})".format(
            self.__class__.__name__, self.name, self.type, self.func
        )

    @cached_property
    def options_map(self) -> OrderedDict:
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_field(self)


class AbstractLink(AbstractBase, ABC):
    pass


LinkType = t.Union[t.Type[TypeRef], t.Type[Optional], t.Type[Sequence]]


def get_type_enum(type_: TypingMeta) -> t.Tuple[Const, str]:
    if isinstance(type_, RefMeta):
        return One, type_.__type_name__
    elif isinstance(type_, OptionalMeta):
        if isinstance(type_.__type__, RefMeta):
            return Maybe, type_.__type__.__type_name__
    elif isinstance(type_, SequenceMeta):
        if isinstance(type_.__item_type__, RefMeta):
            return Many, type_.__item_type__.__type_name__
        elif isinstance(type_.__item_type__, OptionalMeta):
            if isinstance(type_.__item_type__.__type__, RefMeta):
                return MaybeMany, type_.__item_type__.__type__.__type_name__
    raise TypeError("Invalid type specified: {!r}".format(type_))


def is_union(type_: GenericMeta) -> bool:
    if isinstance(type_, OptionalMeta):
        return isinstance(type_.__type__, UnionRefMeta)
    if isinstance(type_, SequenceMeta):
        return is_union(type_.__item_type__)

    return isinstance(type_, UnionRefMeta)


def is_interface(type_: GenericMeta) -> bool:
    if isinstance(type_, OptionalMeta):
        return isinstance(type_.__type__, InterfaceRefMeta)
    if isinstance(type_, SequenceMeta):
        return is_interface(type_.__item_type__)

    return isinstance(type_, InterfaceRefMeta)


def collect_interfaces_types(
    items: t.List["Node"], interfaces: t.List["Interface"]
) -> t.Dict[str, t.List[str]]:
    interfaces_types = defaultdict(list)
    for item in items:
        if item.name is not None and item.implements:
            for impl in item.implements:
                interfaces_types[impl].append(item.name)

    for i in interfaces:
        if i.name not in interfaces_types:
            interfaces_types[i.name] = []

    return dict(interfaces_types)


LT = t.TypeVar("LT", bound=t.Hashable)
LR = t.TypeVar("LR", bound=t.Optional[t.Hashable])

MaybeLink = t.Union[LR, NothingType]
RootLinkT = t.Union[
    # () -> LR
    t.Callable[[], SyncAsync[LR]],
    # (opts) -> LR
    t.Callable[[t.Any], SyncAsync[LR]],
    # (ctx, opts) -> LR
    t.Callable[[t.Any, t.Any], SyncAsync[LR]],
]

LinkT = t.Union[
    # (ids) -> []
    t.Callable[[List[LT]], SyncAsync[LR]],
    # (ids, opts) -> []
    t.Callable[[List[LT], t.Any], SyncAsync[LR]],
    # (ctx, ids) -> []
    t.Callable[[t.Any, List[LT]], SyncAsync[LR]],
    # (ctx, ids, opts) -> []
    t.Callable[[t.Any, List[LT], List], SyncAsync[LR]],
]

RootLinkOne = RootLinkT[LR]
RootLinkMaybe = RootLinkT[MaybeLink[LR]]
RootLinkMany = RootLinkT[List[LR]]  # type: ignore[type-var]

LinkOne = LinkT[LT, List[LR]]  # type: ignore[type-var]
LinkMaybe = LinkT[LT, List[MaybeLink[LR]]]  # type: ignore[type-var]
LinkMany = LinkT[LT, List[List[LR]]]  # type: ignore[type-var]

LinkFunc = t.Union[
    RootLinkOne,
    RootLinkMaybe,
    RootLinkMany,
    LinkOne,
    LinkMaybe,
    LinkMany,
]

LinkOneFunc = t.Union[RootLinkOne, LinkOne]
LinkMaybeFunc = t.Union[RootLinkMaybe, LinkMaybe]
LinkManyFunc = t.Union[RootLinkMany, LinkMany]


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

    @t.overload
    def __init__(
        self,
        name: str,
        type_: t.Type[TypeRef],
        func: LinkOneFunc,
        *,
        requires: t.Optional[t.Union[str, t.List[str]]],
        options: t.Optional[t.Sequence[Option]] = None,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
    ):
        ...

    @t.overload
    def __init__(
        self,
        name: str,
        type_: t.Type[t.Union[UnionRef, InterfaceRef]],
        func: LinkOneFunc,
        *,
        requires: t.Optional[t.Union[str, t.List[str]]],
        options: t.Optional[t.Sequence[Option]] = None,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
    ):
        ...

    @t.overload
    def __init__(
        self,
        name: str,
        type_: t.Type[Optional],
        func: LinkMaybeFunc,
        *,
        requires: t.Optional[t.Union[str, t.List[str]]],
        options: t.Optional[t.Sequence[Option]] = None,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
    ):
        ...

    @t.overload
    def __init__(
        self,
        name: str,
        type_: t.Type[Sequence],
        func: LinkManyFunc,
        *,
        requires: t.Optional[t.Union[str, t.List[str]]],
        options: t.Optional[t.Sequence[Option]] = None,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
    ):
        ...

    def __init__(  # type: ignore[no-untyped-def]
        self,
        name,
        type_,
        func,
        *,
        requires,
        options=None,
        description=None,
        directives=None,
    ):
        """
        :param name: name of the link
        :param type_: type of the link
        :param func: function to load identifiers of the linked node
        :param requires: field name(s) from the current node,
            required to compute identifiers of the linked node
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
        self.is_union = is_union(type_)
        self.is_interface = is_interface(type_)

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, {!r}, ...)".format(
            self.__class__.__name__, self.name, self.type, self.func
        )

    @cached_property
    def options_map(self) -> OrderedDict:
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_link(self)


class AbstractNode(AbstractBase, ABC):
    pass


class Union(AbstractBase):
    def __init__(
        self,
        name: str,
        types: t.List[str],
        *,
        description: t.Optional[str] = None,
    ):
        self.name = name
        self.types = types
        self.description = description

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, ...)".format(
            self.__class__.__name__, self.name, self.types
        )

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_union(self)


class Interface(AbstractBase):
    def __init__(
        self,
        name: str,
        fields: t.List["Field"],
        *,
        description: t.Optional[str] = None,
    ):
        self.name = name
        self.fields = fields
        self.description = description

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, ...)".format(
            self.__class__.__name__, self.name, self.fields
        )

    @cached_property
    def fields_map(self) -> OrderedDict:
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_interface(self)


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

    def __init__(
        self,
        name: t.Optional[str],
        fields: t.List[t.Union[Field, Link]],
        *,
        description: t.Optional[str] = None,
        directives: t.Optional[t.Sequence[SchemaDirective]] = None,
        implements: t.Optional[t.Sequence[str]] = None,
    ):
        """
        :param name: name of the node
        :param fields: list of fields and links
        :param description: description of the node
        :param directives: list of directives for the node
        :param implements: list of interfaces implemented by the node
        """
        self.name = name
        self.fields = fields
        self.description = description
        self.directives: t.Tuple[SchemaDirective, ...] = tuple(directives or ())
        self.implements = tuple(implements or [])

    def __repr__(self) -> str:
        return "{}({!r}, {!r}, ...)".format(
            self.__class__.__name__, self.name, self.fields
        )

    @cached_property
    def fields_map(self) -> OrderedDict:
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_node(self)

    def copy(self) -> "Node":
        return Node(
            name=self.name,
            fields=self.fields[:],
            description=self.description,
            directives=self.directives,
            implements=self.implements,
        )


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

    def __init__(
        self,
        items: t.List[t.Union[Field, Link]],
    ):
        """
        :param items: list of fields, links and singleton nodes
        """
        super(Root, self).__init__(None, items)

    def __repr__(self) -> str:
        return "{}({!r}, {!r})".format(
            self.__class__.__name__, self.name, self.fields
        )

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_root(self)


class AbstractGraph(AbstractBase, ABC):
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

    def __init__(
        self,
        items: t.List[Node],
        data_types: t.Optional[t.Dict[str, t.Type[Record]]] = None,
        directives: t.Optional[t.Sequence[t.Type[SchemaDirective]]] = None,
        unions: t.Optional[t.List[Union]] = None,
        interfaces: t.Optional[t.List[Interface]] = None,
    ):
        """
        :param items: list of nodes
        """
        from .validate.graph import GraphValidator

        if unions is None:
            unions = []

        if interfaces is None:
            interfaces = []

        GraphValidator.validate(items, unions, interfaces)

        self.items = GraphInit.init(items)
        self.unions = unions
        self.interfaces = interfaces
        self.interfaces_types = collect_interfaces_types(self.items, interfaces)
        self.data_types = data_types or {}
        self.__types__ = GraphTypes.get_types(
            self.items, self.unions, self.interfaces, self.data_types
        )
        self.directives: t.Tuple[t.Type[SchemaDirective], ...] = tuple(
            directives or ()
        )

    def __repr__(self) -> str:
        return "{}({!r})".format(self.__class__.__name__, self.items)

    def iter_root(self) -> t.Iterator[t.Union[Field, Link]]:
        for node in self.items:
            if node.name is None:
                for field in node.fields:
                    yield field

    def iter_nodes(self) -> t.Iterator[Node]:
        for node in self.items:
            if node.name is not None:
                yield node

    @cached_property
    def root(self) -> Root:
        return Root(list(self.iter_root()))

    @cached_property
    def nodes(self) -> t.List[Node]:
        return list(self.iter_nodes())

    @cached_property
    def nodes_map(self) -> OrderedDict:
        return OrderedDict((e.name, e) for e in self.iter_nodes())

    @cached_property
    def unions_map(self) -> OrderedDict:
        return OrderedDict((u.name, u) for u in self.unions)

    @cached_property
    def interfaces_map(self) -> OrderedDict:
        return OrderedDict((i.name, i) for i in self.interfaces)

    def accept(self, visitor: "AbstractGraphVisitor") -> t.Any:
        return visitor.visit_graph(self)


class AbstractGraphVisitor(ABC):
    @abstractmethod
    def visit(self, obj: t.Any) -> t.Any:
        pass

    @abstractmethod
    def visit_option(self, obj: Option) -> t.Any:
        pass

    @abstractmethod
    def visit_field(self, obj: Field) -> t.Any:
        pass

    @abstractmethod
    def visit_link(self, obj: Link) -> t.Any:
        pass

    @abstractmethod
    def visit_node(self, obj: Node) -> t.Any:
        pass

    @abstractmethod
    def visit_union(self, obj: Union) -> t.Any:
        pass

    @abstractmethod
    def visit_interface(self, obj: Interface) -> t.Any:
        pass

    @abstractmethod
    def visit_root(self, obj: Root) -> t.Any:
        pass

    @abstractmethod
    def visit_graph(self, obj: Graph) -> t.Any:
        pass


class GraphVisitor(AbstractGraphVisitor):
    def visit(self, obj: t.Any) -> t.Any:
        return obj.accept(self)

    def visit_union(self, obj: "Union") -> t.Any:
        pass

    def visit_interface(self, obj: "Interface") -> t.Any:
        pass

    def visit_option(self, obj: "Option") -> t.Any:
        pass

    def visit_field(self, obj: Field) -> t.Any:
        for option in obj.options:
            self.visit(option)

    def visit_link(self, obj: Link) -> t.Any:
        for option in obj.options:
            self.visit(option)

    def visit_node(self, obj: Node) -> t.Any:
        for item in obj.fields:
            self.visit(item)

    def visit_root(self, obj: Root) -> t.Any:
        for item in obj.fields:
            self.visit(item)

    def visit_graph(self, obj: Graph) -> t.Any:
        for item in obj.items:
            self.visit(item)


class GraphTransformer(AbstractGraphVisitor):
    def visit(self, obj: t.Any) -> t.Any:
        return obj.accept(self)

    def visit_option(self, obj: Option) -> Option:
        return Option(
            obj.name, obj.type, default=obj.default, description=obj.description
        )

    def visit_field(self, obj: Field) -> Field:
        return Field(
            obj.name,
            obj.type,
            obj.func,
            options=[self.visit(op) for op in obj.options],
            description=obj.description,
            directives=obj.directives,
        )

    def visit_link(self, obj: Link) -> Link:
        return Link(
            obj.name,
            obj.type,
            obj.func,
            requires=obj.requires,
            options=[self.visit(op) for op in obj.options],
            description=obj.description,
            directives=obj.directives,
        )

    def visit_node(self, obj: Node) -> Node:
        return Node(
            obj.name,
            [self.visit(f) for f in obj.fields],
            description=obj.description,
            directives=obj.directives,
            implements=obj.implements,
        )

    def visit_union(self, obj: Union) -> Union:
        return Union(
            obj.name,
            obj.types,
            description=obj.description,
        )

    def visit_interface(self, obj: Interface) -> Interface:
        return Interface(
            obj.name,
            obj.fields,
            description=obj.description,
        )

    def visit_root(self, obj: Root) -> Root:
        return Root([self.visit(f) for f in obj.fields])

    def visit_graph(self, obj: Graph) -> Graph:
        return Graph(
            [self.visit(node) for node in obj.items],
            obj.data_types,
            obj.directives,
            obj.unions,
            obj.interfaces,
        )


def apply(graph: Graph, transformers: List[GraphTransformer]) -> Graph:
    """Helper function to apply graph transformations

    Example:

    .. code-block:: python

        graph = hiku.graph.apply(graph, [AsyncGraphQLIntrospection()])

    """
    return reduce(lambda g, tr: tr.visit(g), transformers, graph)


class GraphInit(GraphTransformer):
    @classmethod
    def init(cls, items: t.List[Node]) -> t.List[Node]:
        self = cls()
        return [self.visit(i) for i in items]

    def visit_field(self, obj: Field) -> Field:
        field = super(GraphInit, self).visit_field(obj)
        postprocess = getattr(field.func, "__postprocess__", None)
        if postprocess is not None:
            postprocess(field)
        return field

    def visit_link(self, obj: Link) -> Link:
        link = super(GraphInit, self).visit_link(obj)
        postprocess = getattr(link.func, "__postprocess__", None)
        if postprocess is not None:
            postprocess(link)
        return link


class GraphTypes(GraphVisitor):
    def _visit_graph(
        self,
        items: t.List[Node],
        unions: t.List[Union],
        interfaces: t.List[Interface],
        data_types: t.Dict[str, t.Type[Record]],
    ) -> t.Dict[str, t.Type[Record]]:
        types = OrderedDict(data_types)
        roots = []
        for item in items:
            if item.name is not None:
                types[item.name] = self.visit(item)
            else:
                roots.append(self.visit(item))

        for union in unions:
            types[union.name] = self.visit(union)

        for interface in interfaces:
            types[interface.name] = self.visit(interface)

        types["__root__"] = Record[
            chain.from_iterable(r.__field_types__.items() for r in roots)
        ]
        return types

    @classmethod
    def get_types(
        cls,
        items: t.List[Node],
        unions: t.List[Union],
        interfaces: t.List[Interface],
        data_types: t.Dict[str, t.Type[Record]],
    ) -> t.Dict[str, t.Type[Record]]:
        return cls()._visit_graph(items, unions, interfaces, data_types)

    def visit_graph(self, obj: Graph) -> t.Dict[str, t.Type[Record]]:
        return self._visit_graph(
            obj.items, obj.unions, obj.interfaces, obj.data_types
        )

    def visit_node(self, obj: Node) -> t.Type[Record]:
        return Record[[(f.name, self.visit(f)) for f in obj.fields]]

    def visit_root(self, obj: Root) -> t.Type[Record]:
        return Record[[(f.name, self.visit(f)) for f in obj.fields]]

    def visit_link(self, obj: Link) -> LinkType:
        return obj.type

    def visit_field(self, obj: Field) -> t.Union[FieldType, AnyMeta]:
        return obj.type or Any

    def visit_union(self, obj: Union) -> Union:
        return obj

    def visit_interface(self, obj: Interface) -> Interface:
        return obj
