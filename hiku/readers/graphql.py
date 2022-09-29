import enum

from typing import (
    Optional,
    Dict,
    Iterator,
    Union,
    List,
    cast,
    Any,
    Set,
    Callable,
    Tuple,
)
from functools import lru_cache

from graphql.language import ast
from graphql.language.parser import parse

from ..directives import (
    QueryDirective,
    IncludeDirectiveExt,
    SkipDirectiveExt,
    CachedDirectiveExt,
)
from ..extentions import Extension
from ..query import Node, Field, Link, merge
from ..telemetry.prometheus import (
    QUERY_CACHE_HITS,
    QUERY_CACHE_MISSES,
)


def parse_query(src: str) -> ast.DocumentNode:
    """Parses a query into GraphQL ast

    :param str src: GraphQL query string
    :return: :py:class:`ast.DocumentNode`
    """
    return parse(src)


def wrap_metrics(cached_parser: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> ast.DocumentNode:
        ast = cached_parser(*args, **kwargs)
        info = cached_parser.cache_info()  # type: ignore
        QUERY_CACHE_HITS.set(info.hits)
        QUERY_CACHE_MISSES.set(info.misses)
        return ast
    return wrapper


def setup_query_cache(
    size: int = 128,
) -> None:
    """Sets up lru cache for the ast parsing.

    :param int size: Maximum size of the cache
    """
    global parse_query
    parse_query = lru_cache(maxsize=size)(parse_query)
    parse_query = wrap_metrics(parse_query)


DEFAULT_EXTENSIONS = [
    SkipDirectiveExt(),
    IncludeDirectiveExt(),
    CachedDirectiveExt(),
]


class NodeVisitor:

    def visit(self, obj: ast.Node) -> Any:
        visit_method = getattr(self, 'visit_{}'.format(obj.kind))
        if visit_method is None:
            raise NotImplementedError('Not implemented node type: {!r}'
                                      .format(obj))
        return visit_method(obj)

    def visit_document(self, obj: ast.DocumentNode) -> None:
        for definition in obj.definitions:
            self.visit(definition)

    def visit_operation_definition(
        self, obj: ast.OperationDefinitionNode
    ) -> Any:
        self.visit(obj.selection_set)

    def visit_fragment_definition(
        self, obj: ast.FragmentDefinitionNode
    ) -> Any:
        self.visit(obj.selection_set)

    def visit_selection_set(self, obj: ast.SelectionSetNode) -> Any:
        for i in obj.selections:
            self.visit(i)

    def visit_field(self, obj: ast.FieldNode) -> Any:
        pass

    def visit_fragment_spread(self, obj: ast.FragmentSpreadNode) -> Any:
        pass

    def visit_inline_fragment(self, obj: ast.InlineFragmentNode) -> Any:
        self.visit(obj.selection_set)


class OperationGetter(NodeVisitor):

    def __init__(self, operation_name: Optional[str] = None):
        self._operations: Dict[Optional[str], ast.OperationDefinitionNode] = {}
        self._operation_name = operation_name

    @classmethod
    def get(
        cls,
        doc: ast.DocumentNode,
        operation_name: Optional[str] = None
    ) -> ast.OperationDefinitionNode:
        self = cls(operation_name=operation_name)
        self.visit(doc)
        if not self._operations:
            raise TypeError('No operations in the document')

        if self._operation_name is None:
            if len(self._operations) > 1:
                raise TypeError('Document should contain exactly one operation '
                                'when no operation name was provided')
            return next(iter(self._operations.values()))
        else:
            try:
                return self._operations[self._operation_name]
            except KeyError:
                raise ValueError('Undefined operation name: {!r}'
                                 .format(self._operation_name))

    def visit_fragment_definition(
        self, obj: ast.FragmentDefinitionNode
    ) -> None:
        pass  # skip visit here

    def visit_operation_definition(
        self, obj: ast.OperationDefinitionNode
    ) -> None:
        name = obj.name.value if obj.name is not None else None
        if name in self._operations:
            raise TypeError('Duplicate operation definition: {!r}'
                            .format(name))
        self._operations[name] = obj


class FragmentsCollector(NodeVisitor):

    def __init__(self) -> None:
        self.fragments_map: Dict[str, ast.FragmentDefinitionNode] = {}

    def visit_operation_definition(
        self, obj: ast.OperationDefinitionNode
    ) -> None:
        pass  # not interested in operations here

    def visit_fragment_definition(
        self, obj: ast.FragmentDefinitionNode
    ) -> None:
        if obj.name.value in self.fragments_map:
            raise TypeError('Duplicated fragment name: "{}"'
                            .format(obj.name.value))
        self.fragments_map[obj.name.value] = obj


class SelectionSetVisitMixin:
    extensions: List[Extension]

    def transform_fragment(self, name: str) -> List[Union[Field, Link]]:
        raise NotImplementedError(type(self))

    @property
    def query_variables(self) -> Optional[Dict]:
        raise NotImplementedError(type(self))

    @property
    def query_name(self) -> Optional[str]:
        raise NotImplementedError(type(self))

    def lookup_variable(self, name: str) -> Any:
        try:
            assert self.query_variables is not None
            return self.query_variables[name]
        except KeyError:
            raise TypeError('Variable ${} is not defined in query {}'
                            .format(name, self.query_name or '<unnamed>'))

    def visit_selection_set(
        self, obj: ast.SelectionSetNode
    ) -> Iterator[Union[Field, Link]]:
        for i in obj.selections:
            for j in self.visit(i):  # type: ignore[attr-defined]
                yield j

    def _should_skip(self, directives: List[QueryDirective]) -> bool:
        for d in directives:
            if d.name == 'skip':
                return d.condition  # type: ignore[attr-defined]
            if d.name == 'include':
                return not d.condition  # type: ignore[attr-defined]

        return False

    def _parse_directives(
        self, obj: ast.SelectionNode
    ) -> Tuple[List[QueryDirective], List[QueryDirective]]:
        directives: List[QueryDirective] = []
        builtin_directives: List[QueryDirective] = []
        for ext in self.extensions:
            for directive_obj in obj.directives:
                directive = ext.on_directive_parsing(
                    directive_obj, self
                )
                if directive is not None:
                    if directive.name in ('skip', 'include'):
                        builtin_directives.append(directive)
                    else:
                        directives.append(directive)

        return builtin_directives, directives

    def visit_field(
        self, obj: ast.FieldNode
    ) -> Iterator[Union[Field, Link]]:
        builtin_directives, directives = self._parse_directives(obj)
        if self._should_skip(builtin_directives):
            return

        if obj.arguments:
            options = {arg.name.value: self.visit(arg.value)  # type: ignore[attr-defined] # noqa: E501
                       for arg in obj.arguments}
        else:
            options = None

        if obj.alias is not None:
            alias = obj.alias.value
        else:
            alias = None

        if obj.selection_set is None:
            yield Field(
                obj.name.value, options=options,
                alias=alias, directives=tuple(directives)
            )
        else:
            node = Node(list(self.visit(obj.selection_set)))  # type: ignore[attr-defined] # noqa: E501
            yield Link(
                obj.name.value, node, options=options,
                alias=alias, directives=tuple(directives)
            )

    def visit_variable(self, obj: ast.VariableNode) -> Any:
        return self.lookup_variable(obj.name.value)

    def visit_null_value(self, obj: ast.NullValueNode) -> None:
        return None

    def visit_int_value(self, obj: ast.IntValueNode) -> int:
        return int(obj.value)

    def visit_float_value(self, obj: ast.FloatValueNode) -> float:
        return float(obj.value)

    def visit_string_value(self, obj: ast.StringValueNode) -> str:
        return obj.value

    def visit_boolean_value(self, obj: ast.BooleanValueNode) -> bool:
        return obj.value

    def visit_enum_value(self, obj: ast.EnumValueNode) -> str:
        return obj.value

    def visit_list_value(self, obj: ast.ListValueNode) -> List:
        return [self.visit(i) for i in obj.values]  # type: ignore[attr-defined]

    def visit_object_value(self, obj: ast.ObjectValueNode) -> Dict:
        return {f.name.value: self.visit(f.value) for f in obj.fields}  # type: ignore[attr-defined] # noqa: E501

    def visit_fragment_spread(
        self, obj: ast.FragmentSpreadNode
    ) -> Iterator[Union[Field, Link]]:
        directives, custom = self._parse_directives(obj)
        if self._should_skip(directives):
            return
        for i in self.transform_fragment(obj.name.value):
            yield i

    def visit_inline_fragment(
        self, obj: ast.InlineFragmentNode
    ) -> Iterator[Union[Field, Link]]:
        directives, custom = self._parse_directives(obj)
        if self._should_skip(directives):
            return

        for i in self.visit(obj.selection_set):  # type: ignore[attr-defined]
            yield i


class FragmentsTransformer(SelectionSetVisitMixin, NodeVisitor):
    query_name: str = ''
    query_variables: Dict = {}

    def __init__(
        self,
        document: ast.DocumentNode,
        query_name: str,
        query_variables: Dict,
        extensions: List[Extension],
    ):
        collector = FragmentsCollector()
        collector.visit(document)
        self.query_name = query_name
        self.query_variables = query_variables
        self.fragments_map = collector.fragments_map
        self.cache: Dict[str, List[Union[Field, Link]]] = {}
        self.pending_fragments: Set[str] = set()
        self.extensions = extensions

    def transform_fragment(self, name: str) -> List[Union[Field, Link]]:
        return self.visit(self.fragments_map[name])

    def visit_operation_definition(
        self, obj: ast.OperationDefinitionNode
    ) -> None:
        pass  # not interested in operations here

    def visit_fragment_definition(
        self, obj: ast.FragmentDefinitionNode
    ) -> List[Union[Field, Link]]:
        if obj.name.value in self.cache:
            return self.cache[obj.name.value]
        else:
            if obj.name.value in self.pending_fragments:
                raise TypeError('Cyclic fragment usage: "{}"'
                                .format(obj.name.value))
            self.pending_fragments.add(obj.name.value)
            try:
                selection_set = list(self.visit(obj.selection_set))
            finally:
                self.pending_fragments.discard(obj.name.value)
            self.cache[obj.name.value] = selection_set
            return selection_set


class GraphQLTransformer(SelectionSetVisitMixin, NodeVisitor):
    query_name: Optional[str] = None
    query_variables: Optional[Dict[str, Any]] = None
    fragments_transformer = None

    def __init__(
        self,
        document: ast.DocumentNode,
        variables: Optional[Dict] = None,
        extensions: Optional[List[Extension]] = None
    ):
        self.document = document
        self.variables = variables
        self.extensions = DEFAULT_EXTENSIONS + (extensions or [])

    @classmethod
    def transform(
        cls,
        document: ast.DocumentNode,
        op: ast.OperationDefinitionNode,
        variables: Optional[Dict] = None,
        extensions: Optional[List[Extension]] = None
    ) -> Node:
        visitor = cls(document, variables, extensions)
        return visitor.visit(op)

    def transform_fragment(self, name: str) -> List[Union[Field, Link]]:
        assert self.fragments_transformer
        return self.fragments_transformer.transform_fragment(name)

    def visit_operation_definition(
        self, obj: ast.OperationDefinitionNode
    ) -> Node:
        variables = self.variables or {}
        query_name = obj.name.value if obj.name else '<unnamed>'
        query_variables = {}
        for var_defn in obj.variable_definitions or ():
            name = var_defn.variable.name.value
            try:
                value = variables[name]  # TODO: check variable type
            except KeyError:
                if var_defn.default_value is not None:
                    value = self.visit(var_defn.default_value)
                elif isinstance(var_defn.type, ast.NonNullTypeNode):
                    raise TypeError('Variable "{}" is not provided for query {}'
                                    .format(name, query_name))
                else:
                    value = None
            query_variables[name] = value

        self.query_name = query_name
        assert self.query_name is not None
        self.query_variables = query_variables
        self.fragments_transformer = FragmentsTransformer(self.document,
                                                          self.query_name,
                                                          self.query_variables,
                                                          self.extensions)
        ordered = obj.operation is ast.OperationType.MUTATION
        try:
            node = Node(list(self.visit(obj.selection_set)),
                        ordered=ordered)
        finally:
            self.query_name = None
            self.query_variables = None
            self.fragments_transformer = None
        return merge([node])


def read(
    src: str,
    variables: Optional[Dict] = None,
    operation_name: Optional[str] = None,
    extensions: Optional[List[Extension]] = None
) -> Node:
    """Reads a query from the GraphQL document

    Example:

    .. code-block:: python

        query = read('{ foo bar }')
        result = engine.execute(graph, query)

    :param str src: GraphQL query
    :param dict variables: query variables
    :param str operation_name: Name of the operation to execute
    :return: :py:class:`hiku.query.Node`, ready to execute query object
    """
    doc = parse_query(src)
    op = OperationGetter.get(doc, operation_name=operation_name)
    if op.operation is not ast.OperationType.QUERY:
        raise TypeError('Only "query" operations are supported, '
                        '"{}" operation was provided'
                        .format(op.operation.value))

    return GraphQLTransformer.transform(doc, op, variables, extensions)


class OperationType(enum.Enum):
    """Enumerates GraphQL operation types"""
    #: query operation
    QUERY = ast.OperationType.QUERY
    #: mutation operation
    MUTATION = ast.OperationType.MUTATION
    #: subscription operation
    SUBSCRIPTION = ast.OperationType.SUBSCRIPTION


class Operation:
    """Represents requested GraphQL operation"""
    def __init__(
        self,
        type_: OperationType,
        query: Node,
        name: Optional[str] = None
    ):
        #: type of the operation
        self.type = type_
        #: operation's query
        self.query = query
        #: optional name of the operation
        self.name = name


def read_operation(
    src: str,
    variables: Optional[Dict] = None,
    operation_name: Optional[str] = None,
    extensions: Optional[List[Extension]] = None
) -> Operation:
    """Reads an operation from the GraphQL document

    Example:

    .. code-block:: python

        op = read_operation('{ foo bar }')
        if op.type is OperationType.QUERY:
            result = engine.execute(query_graph, op.query)

    :param str src: GraphQL document
    :param dict variables: query variables
    :param str operation_name: Name of the operation to execute
    :return: :py:class:`Operation`
    """
    doc = parse_query(src)
    op = OperationGetter.get(doc, operation_name=operation_name)
    query = GraphQLTransformer.transform(doc, op, variables, extensions)
    type_ = cast(Optional[OperationType], (
        OperationType._value2member_map_.get(op.operation)
    ))
    name = op.name.value if op.name else None
    if type_ is None:
        raise TypeError('Unsupported operation type: {}'.format(op.operation))

    return Operation(type_, query, name)
